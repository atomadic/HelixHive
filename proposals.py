"""
Proposals Engine for HelixHive Phase 1.
Scans HelixDB for new proposals, evaluates them with fitness predictor,
submits to council, and applies approved changes atomically.
Includes integration with Revelation Engine for synthetic proposals.
"""

import uuid
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

import yaml

from agent import Agent
from council import Council
from fitness import FitnessPredictor
from revelation import RevelationEngine
import helixdb

logger = logging.getLogger(__name__)


class ProposalError(Exception):
    """Raised when a proposal cannot be processed."""
    pass


def process_proposals(db: 'helixdb.HelixDB',
                     agents: List[Agent],
                     genome: Any,
                     config: Any) -> List[Dict]:
    """
    Main entry point: scan for new proposals and process them.
    Modifies db and genome in-place; caller must commit after.
    Returns list of processed proposal records.
    """
    # Load configuration from genome
    max_proposals = genome.data.get('proposals', {}).get('max_per_heartbeat', 10)
    fitness_threshold = genome.data.get('proposals', {}).get('fitness_threshold', 0.0)  # No filter by default
    use_revelation = genome.data.get('revelation', {}).get('enabled', False)

    # Get last processed proposal time from genome
    last_time = genome.data.get('last_proposal_time', 0)
    
    # Find all nodes of type 'Proposal'
    proposal_nodes = db.query_nodes_by_label('Proposal')
    # Sort by timestamp
    proposal_nodes.sort(key=lambda n: n.properties.get('timestamp', 0))
    
    processed = []
    count = 0
    for node in proposal_nodes:
        if count >= max_proposals:
            logger.info(f"Reached max proposals per heartbeat ({max_proposals})")
            break
        props = node.properties
        ts = props.get('timestamp', 0)
        if ts <= last_time:
            continue
        
        # Process this proposal
        result = _process_single_proposal(db, agents, genome, config, node, fitness_threshold)
        processed.append(result)
        last_time = max(last_time, ts)
        count += 1
    
    # Optionally generate a synthetic proposal using Revelation Engine
    if use_revelation and count < max_proposals:
        try:
            syn_result = _generate_synthetic_proposal(db, agents, genome, config)
            if syn_result:
                processed.append(syn_result)
        except Exception as e:
            logger.error(f"Synthetic proposal generation failed: {e}")
    
    # Update genome with last processed time
    genome.data['last_proposal_time'] = last_time
    # No commit here; caller will commit
    
    return processed


def _process_single_proposal(db: 'helixdb.HelixDB',
                            agents: List[Agent],
                            genome: Any,
                            config: Any,
                            proposal_node: 'helixdb.Node',
                            fitness_threshold: float) -> Dict:
    """
    Process one proposal node.
    Returns record of processing.
    """
    props = proposal_node.properties
    proposal_id = proposal_node.id
    ptype = props.get('type')
    proposer_id = props.get('proposer_id')
    description = props.get('description', '')
    tags = props.get('tags', [])
    changes = props.get('changes', {})
    
    logger.info(f"Processing proposal {proposal_id} of type {ptype} from {proposer_id}")
    
    # Basic validation
    if not ptype:
        raise ProposalError("Proposal missing type")
    
    # Compute fitness score
    fitness_score = 0.5
    confidence = 0.0
    try:
        predictor = FitnessPredictor(db, genome)
        # For proposals, we use proposer's Leech vector if available
        proposer_node = db.get_node(proposer_id) if proposer_id else None
        if proposer_node and 'leech' in proposer_node.vectors:
            target_vec = proposer_node.vectors['leech']
            context = {
                'phase': genome.data.get('helicity', {}).get('current_phase', 0),
                'description': description
            }
            fitness_score, confidence = predictor.predict('proposal', proposal_id,
                                                         target_vector=target_vec,
                                                         context=context)
        else:
            # Fallback: use average fitness of recent proposals
            fitness_score = 0.5
            confidence = 0.1
    except Exception as e:
        logger.warning(f"Fitness prediction failed: {e}")
        fitness_score = 0.5
        confidence = 0.0
    
    # Optional pre-filter by fitness (if threshold > 0)
    if fitness_score < fitness_threshold:
        logger.info(f"Proposal {proposal_id} fitness {fitness_score} below threshold {fitness_threshold}, skipping")
        return {
            'proposal_id': proposal_id,
            'approved': False,
            'fitness_score': fitness_score,
            'confidence': confidence,
            'reason': 'fitness_below_threshold',
            'timestamp': datetime.now().timestamp()
        }
    
    # Prepare proposal dict for council
    council_proposal = {
        'id': proposal_id,
        'type': ptype,
        'description': description,
        'tags': tags,
        'fitness_score': fitness_score,
        'confidence': confidence,
        'changes': changes
    }
    
    # Submit to council
    council = Council(genome)
    approved, transcript = council.vote(council_proposal)
    
    # Record outcome
    outcome = {
        'proposal_id': proposal_id,
        'approved': approved,
        'fitness_score': fitness_score,
        'confidence': confidence,
        'transcript': transcript,
        'timestamp': datetime.now().timestamp()
    }
    
    # If approved, apply changes
    if approved:
        try:
            _apply_proposal(db, agents, genome, ptype, changes, proposer_id)
            outcome['applied'] = True
            logger.info(f"Proposal {proposal_id} approved and applied")
        except Exception as e:
            logger.error(f"Failed to apply proposal {proposal_id}: {e}")
            outcome['applied'] = False
            outcome['error'] = str(e)
    else:
        logger.info(f"Proposal {proposal_id} rejected")
        outcome['applied'] = False
    
    # Store outcome as a node linked to proposal
    outcome_id = db.add_node('ProposalOutcome', properties=outcome)
    db.add_edge(proposal_id, outcome_id, 'HAS_OUTCOME')
    
    return outcome


def _generate_synthetic_proposal(db: 'helixdb.HelixDB',
                                 agents: List[Agent],
                                 genome: Any,
                                 config: Any) -> Optional[Dict]:
    """
    Use Revelation Engine to generate a synthetic agent proposal.
    Returns outcome dict if proposal was created and approved.
    """
    # Only generate if there are agents to provide context
    if not agents:
        logger.debug("No agents available for synthetic proposal generation")
        return None
    
    # Build context from current state
    recent_proposals = _get_recent_proposals(db, limit=5)
    factions = _get_faction_info(db, agents)
    
    context = {
        'phase': genome.data.get('helicity', {}).get('current_phase', 0),
        'recent_proposals': recent_proposals,
        'factions': factions,
        'health': 'stable',  # could compute
        'agent_count': len(agents)
    }
    
    # Run Revelation Engine
    engine = RevelationEngine(db, genome, config)
    proposal_data = engine.generate(context)
    
    if not proposal_data or proposal_data.get('rating', 0) < 0.6:
        logger.debug("Synthetic proposal rating too low, discarding")
        return None
    
    # Create a synthetic agent proposal
    syn_proposal_id = str(uuid.uuid4())
    syn_proposal = {
        'id': syn_proposal_id,
        'type': 'synthetic_agent',
        'proposer_id': None,  # system-generated
        'description': proposal_data.get('summary', 'Synthetic agent proposal'),
        'tags': ['synthetic', 'revelation'],
        'changes': {
            'genome': {
                'role': proposal_data.get('role', 'synthetic'),
                'prompt': proposal_data.get('details', 'You are a synthetic agent.'),
                'traits': proposal_data.get('traits', {})
            }
        },
        'timestamp': datetime.now().timestamp()
    }
    
    # Add proposal node to DB
    db.add_node('Proposal', syn_proposal_id, properties=syn_proposal)
    
    # Process it immediately (recursive call but careful)
    # We'll process it as a normal proposal
    # Create a dummy node for processing
    class DummyNode:
        def __init__(self, nid, props):
            self.id = nid
            self.properties = props
    node = DummyNode(syn_proposal_id, syn_proposal)
    return _process_single_proposal(db, agents, genome, config, node, fitness_threshold=0.0)


def _apply_proposal(db: 'helixdb.HelixDB',
                   agents: List[Agent],
                   genome: Any,
                   ptype: str,
                   changes: Dict,
                   proposer_id: Optional[str]):
    """
    Apply an approved proposal's changes.
    Modifies db, agents list, and genome in-place.
    """
    if ptype == 'genome':
        _apply_genome_proposal(db, genome, changes)
    elif ptype == 'agent':
        _apply_agent_proposal(db, agents, changes)
    elif ptype == 'breed':
        _apply_breed_proposal(db, agents, genome, changes, proposer_id)
    elif ptype == 'merge':
        _apply_merge_proposal(db, agents, changes, proposer_id)
    elif ptype == 'synthetic_agent':
        _apply_synthetic_proposal(db, agents, changes, proposer_id)
    else:
        raise ProposalError(f"Unknown proposal type: {ptype}")


def _apply_genome_proposal(db: 'helixdb.HelixDB', genome: Any, changes: Dict):
    """Update genome parameters."""
    params = changes.get('parameters', {})
    for key, value in params.items():
        # Support nested updates? For Phase 1, simple top-level only.
        genome.data[key] = value
    logger.info(f"Genome updated: {params}")


def _apply_agent_proposal(db: 'helixdb.HelixDB', agents: List[Agent], changes: Dict):
    """Modify an existing agent."""
    agent_id = changes.get('agent_id')
    if not agent_id:
        raise ProposalError("Agent proposal missing agent_id")
    
    # Find agent in list
    agent = next((a for a in agents if a.agent_id == agent_id), None)
    if not agent:
        # Try loading from DB
        node = db.get_node(agent_id)
        if node:
            agent = Agent.load_from_db(db, agent_id)
            agents.append(agent)
        else:
            raise ProposalError(f"Agent {agent_id} not found")
    
    # Update fields
    if 'prompt' in changes:
        agent.prompt = changes['prompt']
    if 'traits' in changes:
        # Clamp trait values to [0,1]
        for key, val in changes['traits'].items():
            agent.traits[key] = max(0.0, min(1.0, val))
    # Recompute state vectors
    agent.compute_state_vectors()
    agent.record_activity()
    # Save to DB (will be committed later)
    agent.save_to_db(db)
    logger.info(f"Agent {agent_id} updated")


def _apply_breed_proposal(db: 'helixdb.HelixDB', agents: List[Agent],
                          genome: Any, changes: Dict, proposer_id: Optional[str]):
    """Create a new agent by breeding two parents."""
    parent1_id = changes.get('parent1')
    parent2_id = changes.get('parent2')
    new_role = changes.get('new_role', 'hybrid')
    
    if not parent1_id or not parent2_id:
        raise ProposalError("Breed proposal missing parent IDs")
    
    # Find parents
    parent1 = _find_agent(db, agents, parent1_id)
    parent2 = _find_agent(db, agents, parent2_id)
    
    # Get current phase and mutation params from genome
    phase = genome.data.get('helicity', {}).get('current_phase', 0)
    mutation_rate = genome.data.get('mutation', {}).get('base_rate', 0.1)
    bias = genome.data.get('helicity', {}).get('mutation_bias', 0.05)
    
    # Create child
    child = Agent.breed(parent1, parent2, new_role, mutation_rate, phase, bias)
    child.save_to_db(db)
    agents.append(child)
    logger.info(f"New agent bred: {child.agent_id} from {parent1_id} and {parent2_id}")


def _apply_merge_proposal(db: 'helixdb.HelixDB', agents: List[Agent],
                          changes: Dict, proposer_id: Optional[str]):
    """Merge two agents into one (archive originals)."""
    agent1_id = changes.get('agent1')
    agent2_id = changes.get('agent2')
    new_role = changes.get('new_role', 'merged')
    
    if not agent1_id or not agent2_id:
        raise ProposalError("Merge proposal missing agent IDs")
    
    # Find agents
    agent1 = _find_agent(db, agents, agent1_id)
    agent2 = _find_agent(db, agents, agent2_id)
    
    # Average traits
    new_traits = {}
    all_keys = set(agent1.traits.keys()) | set(agent2.traits.keys())
    for key in all_keys:
        v1 = agent1.traits.get(key, 0.5)
        v2 = agent2.traits.get(key, 0.5)
        new_traits[key] = (v1 + v2) / 2.0
    
    # Create new agent
    child = Agent(
        role=new_role,
        prompt=agent1.prompt,  # arbitrary choice
        traits=new_traits,
        generation=max(agent1.generation, agent2.generation) + 1,
        parents=[agent1_id, agent2_id]
    )
    child.save_to_db(db)
    agents.append(child)
    
    # Archive originals (mark as inactive)
    agent1.epigenetic_marks['archived'] = True
    agent2.epigenetic_marks['archived'] = True
    agent1.save_to_db(db)
    agent2.save_to_db(db)
    logger.info(f"Merged agents into {child.agent_id}")


def _apply_synthetic_proposal(db: 'helixdb.HelixDB', agents: List[Agent],
                              changes: Dict, proposer_id: Optional[str]):
    """Create a new agent from a synthetic genome (generated by Evo2/Revelation)."""
    genome_data = changes.get('genome')
    if not genome_data:
        raise ProposalError("Synthetic agent proposal missing genome")
    
    # genome_data should contain role, prompt, traits
    role = genome_data.get('role', 'synthetic')
    prompt = genome_data.get('prompt', 'You are a synthetic agent.')
    traits = genome_data.get('traits', {})
    
    # Clamp traits
    for key, val in traits.items():
        traits[key] = max(0.0, min(1.0, val))
    
    child = Agent(
        role=role,
        prompt=prompt,
        traits=traits,
        synthetic=True,
        parents=[proposer_id] if proposer_id else []
    )
    child.save_to_db(db)
    agents.append(child)
    logger.info(f"Synthetic agent created: {child.agent_id}")


def _find_agent(db: 'helixdb.HelixDB', agents: List[Agent], agent_id: str) -> Agent:
    """Helper to find an agent in list or load from DB."""
    agent = next((a for a in agents if a.agent_id == agent_id), None)
    if not agent:
        node = db.get_node(agent_id)
        if node:
            agent = Agent.load_from_db(db, agent_id)
            agents.append(agent)
        else:
            raise ProposalError(f"Agent {agent_id} not found")
    return agent


def _get_recent_proposals(db: 'helixdb.HelixDB', limit: int = 5) -> List[str]:
    """Get summaries of recent successful proposals."""
    nodes = db.query_nodes_by_label('ProposalOutcome')
    # Filter approved
    approved = [n for n in nodes if n.properties.get('approved')]
    approved.sort(key=lambda n: n.properties.get('timestamp', 0), reverse=True)
    summaries = []
    for n in approved[:limit]:
        # Get linked proposal
        edges = db.query_edges(dst=n.id, label='HAS_OUTCOME')
        if edges:
            prop_id = edges[0][0]  # src
            prop_node = db.get_node(prop_id)
            if prop_node:
                summaries.append(prop_node.properties.get('description', '')[:100])
    return summaries


def _get_faction_info(db: 'helixdb.HelixDB', agents: List[Agent]) -> str:
    """Simple faction info: count of factions from genome."""
    # In Phase 1, we don't have real factions; just return placeholder
    return "No faction data”
