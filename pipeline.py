"""
Product Pipeline for HelixHive – creates, refines, and approves products.
Agents generate products, refine them through multiple rounds, and submit to council.
Phase 1 implementation with simplified scoring and agent selection.
If no suitable creator exists, spawns and trains a new agent using Revelation Engine (if available) or a default.
"""

import logging
import time
from typing import List, Optional, Dict, Any
from pathlib import Path

import numpy as np

from agent import Agent
from council import Council
from fitness import FitnessPredictor
from llm import call_llm
from memory import HD, LeechProjection
import helixdb
from revelation import RevelationEngine  # Optional, for training

logger = logging.getLogger(__name__)

# Directory for approved products (set by orchestrator)
PRODUCTS_DIR = Path("products")


def run_pipeline(niche: str,
                 agents: List[Agent],
                 genome: Any,
                 config: Any,
                 db: Optional['helixdb.HelixDB'] = None) -> Optional[Dict]:
    """
    Run the product pipeline for a given niche.
    If no suitable creator agent exists, spawns and trains a new agent.

    Args:
        niche: product category/topic
        agents: list of active agents (will be modified if reputation changes or new agent added)
        genome: genome object containing pipeline parameters
        config: config object
        db: optional HelixDB for storing product metadata and Revelation Engine

    Returns:
        Outcome dictionary if pipeline completed, None if aborted.
    """
    # Check if pipeline is enabled in genome
    if not genome.data.get('pipeline', {}).get('enabled', True):
        logger.debug("Product pipeline is disabled in genome")
        return None

    # Ensure we have at least one agent; if not, spawn a default
    if len(agents) == 0:
        logger.warning("No agents available. Spawning default agent.")
        default_agent = _spawn_default_agent(db, genome)
        agents.append(default_agent)

    # Select creator agent
    creator = _select_creator(agents, genome, db, niche)
    if not creator:
        logger.error("No suitable creator found even after spawning attempt.")
        return None

    logger.info(f"Creator: {creator.role} ({creator.agent_id[:8]})")

    # Step 1: Create initial product
    product = _create_product(creator, niche)
    if not product:
        logger.error("Product creation failed")
        creator.failures += 1
        creator.record_activity()
        if db:
            creator.save_to_db(db)
        return None

    # Step 2: Refinement rounds
    num_rounds = genome.data.get('pipeline', {}).get('refinement_rounds', 3)
    used_agent_ids = [creator.agent_id]  # track agents used to avoid repetition

    for round_num in range(num_rounds):
        # Select a refiner different from creator and previous refiners
        refiner = _select_refiner(agents, used_agent_ids, genome)
        if not refiner:
            logger.warning("No suitable refiner found, skipping remaining refinement rounds")
            break

        used_agent_ids.append(refiner.agent_id)
        logger.info(f"Refinement round {round_num+1} by {refiner.role}")

        feedback = _generate_feedback(product, refiner)
        if not feedback:
            logger.warning(f"Feedback generation failed for round {round_num+1}")
            continue

        product = _refine_product(product, feedback, refiner)
        if not product:
            logger.warning(f"Refinement failed for round {round_num+1}")
            break

    # Step 3: Score the product
    score = _score_product(product, genome, db)
    logger.info(f"Product score: {score:.3f}")

    # Step 4: Create proposal for council
    proposal = _create_product_proposal(product, creator, niche, score)

    # Step 5: Council vote
    council = Council(genome)
    approved, transcript = council.vote(proposal)

    # Step 6: Handle outcome
    if approved:
        outcome = _handle_approval(product, creator, proposal, transcript, db)
        logger.info(f"Product approved, saved to {outcome['path']}")
        return outcome
    else:
        logger.info("Product rejected by council")
        creator.failures += 1
        creator.record_activity()
        if db:
            creator.save_to_db(db)
        return {
            'approved': False,
            'creator': creator.agent_id,
            'transcript': transcript,
            'score': score
        }


def _spawn_default_agent(db: Optional['helixdb.HelixDB'], genome: Any) -> Agent:
    """
    Create a default agent when none exist.
    If Revelation Engine is available, use it to generate a more sophisticated agent.
    """
    # Check if Revelation Engine is enabled and we have a DB
    rev_enabled = genome.data.get('revelation', {}).get('enabled', False)
    if rev_enabled and db:
        try:
            # Build minimal context for revelation
            context = {
                'phase': genome.data.get('helicity', {}).get('current_phase', 0),
                'recent_proposals': '',
                'factions': '',
                'health': 'bootstrap',
                'agent_count': 0
            }
            engine = RevelationEngine(db, genome, None)  # config not needed for generation
            proposal_data = engine.generate(context)
            if proposal_data and proposal_data.get('rating', 0) > 0.6:
                # Use generated data to create agent
                role = proposal_data.get('role', 'default_creator')
                prompt = proposal_data.get('details', 'You are a creative product generator.')
                traits = proposal_data.get('traits', {})
                # Ensure traits are within bounds
                for k in traits:
                    traits[k] = max(0.0, min(1.0, traits[k]))
                agent = Agent(
                    role=role,
                    prompt=prompt,
                    traits=traits,
                    generation=0,
                    synthetic=True
                )
                if db:
                    agent.save_to_db(db)
                logger.info(f"Spawned synthetic default agent: {agent.role}")
                return agent
        except Exception as e:
            logger.warning(f"Revelation Engine failed for default agent: {e}")

    # Fallback: create a simple default agent
    agent = Agent(
        role="default_creator",
        prompt="You are a creative product generator. Create detailed, innovative products.",
        traits={"creativity": 0.7, "thoroughness": 0.7, "cooperativeness": 0.5},
        generation=0,
        synthetic=False
    )
    if db:
        agent.save_to_db(db)
    logger.info("Spawned fallback default agent")
    return agent


def _select_creator(agents: List[Agent], genome: Any,
                    db: Optional['helixdb.HelixDB'], niche: str) -> Optional[Agent]:
    """
    Select the creator agent.
    Phase 1: returns the first agent. If no agents, attempts to spawn one.
    """
    if not agents:
        return _spawn_default_agent(db, genome)
    # Simple: return first agent
    return agents[0]


def _select_refiner(agents: List[Agent], used_ids: List[str], genome: Any) -> Optional[Agent]:
    """
    Select a refiner agent not in used_ids.
    Phase 1: return the first eligible agent.
    """
    for agent in agents:
        if agent.agent_id not in used_ids:
            return agent
    return None


def _create_product(agent: Agent, niche: str) -> Optional[str]:
    """Use agent to generate an initial product."""
    system = f"You are {agent.role}, a creative product generator. Your traits: {agent.traits}"
    prompt = (f"Create a detailed, innovative product for the niche: {niche}. "
              f"Include a title, description, key features, and a sample output. "
              f"Be creative and comprehensive. Aim for at least 300 words.")

    try:
        product = call_llm(prompt, system=system, max_tokens=2000, temperature=0.8)
        return product
    except Exception as e:
        logger.error(f"Product creation LLM failed: {e}")
        return None


def _generate_feedback(product: str, agent: Agent) -> Optional[str]:
    """Generate constructive feedback on a product."""
    system = f"You are {agent.role}, a critical reviewer. Provide constructive feedback to improve the product."
    prompt = f"Product:\n{product}\n\nProvide specific, actionable feedback to make this product better. Focus on clarity, novelty, and completeness."

    try:
        feedback = call_llm(prompt, system=system, max_tokens=800, temperature=0.7)
        return feedback
    except Exception as e:
        logger.error(f"Feedback generation failed: {e}")
        return None


def _refine_product(product: str, feedback: str, agent: Agent) -> Optional[str]:
    """Refine product based on feedback."""
    system = f"You are {agent.role}, a perfectionist refiner. Improve the product based on the feedback while preserving its core ideas."
    prompt = f"Original product:\n{product}\n\nFeedback:\n{feedback}\n\nCreate an improved version. Maintain the original structure but enhance as suggested."

    try:
        refined = call_llm(prompt, system=system, max_tokens=2000, temperature=0.7)
        return refined
    except Exception as e:
        logger.error(f"Refinement failed: {e}")
        return None


def _score_product(product: str, genome: Any, db: Optional['helixdb.HelixDB']) -> float:
    """
    Compute a quality score for the product (0-1).
    Phase 1: uses word count normalized, optionally enhanced by E8 scoring.
    """
    # Word count score (simplest quality proxy)
    word_count = len(product.split())
    max_words = genome.data.get('pipeline', {}).get('max_product_words', 1500)
    word_score = min(1.0, word_count / max_words)

    e8_enabled = genome.data.get('features', {}).get('e8_scoring', False)
    if e8_enabled and db:
        try:
            # Compute Leech vector for product (bag-of-words)
            words = product.split()[:200]  # limit for efficiency
            if not words:
                return word_score

            word_vecs = [HD.from_word(w) for w in words]
            hd_vec = HD.bundle(word_vecs)
            leech_vec = LeechProjection.project(hd_vec)

            # Use fitness predictor to score the product
            predictor = FitnessPredictor(db, genome)
            temp_id = f"temp_prod_{int(time.time())}"
            fitness, confidence = predictor.predict('product', temp_id,
                                                    target_vector=leech_vec,
                                                    context={'text': product[:500]})
            weight = confidence if confidence > 0 else 0.3
            return (1 - weight) * word_score + weight * fitness
        except Exception as e:
            logger.warning(f"Advanced scoring failed: {e}, falling back to word count")
            return word_score
    else:
        return word_score


def _create_product_proposal(product: str, creator: Agent, niche: str, score: float) -> Dict:
    """Create a proposal dict for council vote."""
    return {
        'id': f"prod_{int(time.time())}_{creator.agent_id[:8]}",
        'type': 'product',
        'description': f"Approve product for niche '{niche}' (score: {score:.2f})",
        'tags': ['product', 'safe'],
        'fitness_score': score,
        'confidence': 0.8,
        'changes': {},
        'product_excerpt': product[:500] + "..." if len(product) > 500 else product
    }


def _handle_approval(product: str, creator: Agent, proposal: Dict,
                     transcript: str, db: Optional['helixdb.HelixDB']) -> Dict:
    """Handle approved product: save to disk, update reputation, record in DB."""
    timestamp = int(time.time())
    safe_desc = "".join(c for c in proposal['description'][:40] if c.isalnum() or c in (' ', '-')).rstrip()
    folder_name = f"{timestamp}_{safe_desc.replace(' ', '_')}"
    folder = PRODUCTS_DIR / folder_name
    folder.mkdir(parents=True, exist_ok=True)

    product_path = folder / "product.txt"
    transcript_path = folder / "transcript.txt"
    with open(product_path, 'w', encoding='utf-8') as f:
        f.write(product)
    with open(transcript_path, 'w', encoding='utf-8') as f:
        f.write(transcript)

    creator.reputation += 10
    creator.record_activity()
    if db:
        creator.save_to_db(db)

    if db:
        prod_node_id = db.add_node(
            label='Product',
            properties={
                'path': str(product_path),
                'niche': proposal['description'],
                'creator': creator.agent_id,
                'timestamp': timestamp,
                'score': proposal.get('fitness_score', 0),
                'word_count': len(product.split())
            }
        )
        db.add_edge(creator.agent_id, prod_node_id, 'CREATED')

    return {
        'approved': True,
        'path': str(folder),
        'creator': creator.agent_id,
        'transcript': transcript,
        'score': proposal.get('fitness_score', 0)
    }
