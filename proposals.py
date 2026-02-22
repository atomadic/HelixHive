"""
Proposals Engine for HelixHive Phase 2.
Scans for new proposal nodes, predicts fitness, submits to council,
and applies approved changes atomically.
Supports proposal types: genome, agent, breed, merge, synthetic_agent, model, user_product.
"""

import logging
import time
import uuid
from typing import Dict, List, Any, Optional

from agent import Agent
from council import Council
from fitness import FitnessPredictor
from genome import Genome
from model_proposals import handle_approved_model
from user_requests import handle_approved_user_request  # to be implemented
from helixdb_git_adapter import HelixDBGit

logger = logging.getLogger(__name__)


class ProposalError(Exception):
    """Raised when a proposal cannot be processed."""
    pass


def process_proposals(db: HelixDBGit, agents: List[Agent], genome: Genome,
                      config: Any) -> List[Dict]:
    """
    Main entry point: scan for pending proposals and process them.
    Returns list of outcome records.
    """
    # Load configuration
    max_proposals = genome.data.get('proposals', {}).get('max_per_heartbeat', 10)
    fitness_threshold = genome.data.get('proposals', {}).get('fitness_threshold', 0.0)

    # Find all pending proposals
    proposal_nodes = db.get_nodes_by_type('Proposal')
    pending = [node for node in proposal_nodes.values() if node.get('status') == 'pending']
    # Sort by timestamp (oldest first)
    pending.sort(key=lambda n: n.get('timestamp', 0))

    processed = []
    count = 0
    for node in pending:
        if count >= max_proposals:
            logger.info(f"Reached max proposals per heartbeat ({max_proposals})")
            break

        # Mark as processing to avoid duplicate (atomic update)
        node['status'] = 'processing'
        db.update_properties(node['id'], {'status': 'processing'})

        try:
            outcome = _process_single_proposal(db, agents, genome, config, node, fitness_threshold)
            processed.append(outcome)
            count += 1
        except Exception as e:
            logger.error(f"Failed to process proposal {node['id']}: {e}")
            # Mark as failed
            node['status'] = 'failed'
            node['error'] = str(e)
            db.update_properties(node['id'], {'status': 'failed', 'error': str(e)})

    return processed


def _process_single_proposal(db: HelixDBGit, agents: List[Agent],
                             genome: Genome, config: Any,
                             proposal_node: Dict, fitness_threshold: float) -> Dict:
    """Process one proposal node."""
    proposal_id = proposal_node['id']
    props = proposal_node
    ptype = props.get('type')
    proposer_id = props.get('proposer_id')
    description = props.get('description', '')
    tags = props.get('tags', [])
    changes = props.get('changes', {})

    logger.info(f"Processing proposal {proposal_id} of type {ptype} from {proposer_id}")

    if not ptype:
        raise ProposalError("Proposal missing type")

    # Compute fitness score
    fitness_score = 0.5
    confidence = 0.0
    try:
        predictor = FitnessPredictor(db, genome)
        # For proposals, use proposer's Leech vector if available
        if proposer_id:
            proposer_node = db.get_node(proposer_id)
            if proposer_node and proposer_node.get('leech_vector') is not None:
                target_vec = proposer_node['leech_vector']
                context = {
                    'phase': genome.data.get('helicity', {}).get('current_phase', 0),
                    'description': description,
                    'tags': tags
                }
                fitness_score, confidence = predictor.predict('proposal', proposal_id,
                                                             target_vector=target_vec,
                                                             context=context)
            else:
                # Fallback: average fitness of recent proposals
                fitness_score = 0.5
                confidence = 0.1
    except Exception as e:
        logger.warning(f"Fitness prediction failed: {e}")
        fitness_score = 0.5
        confidence = 0.0

    # Optional pre-filter by fitness
    if fitness_score < fitness_threshold:
        logger.info(f"Proposal {proposal_id} fitness {fitness_score} below threshold {fitness_threshold}")
        outcome = {
            'proposal_id': proposal_id,
            'approved': False,
            'fitness_score': fitness_score,
            'confidence': confidence,
            'reason': 'fitness_below_threshold',
            'timestamp': time.time()
        }
        _store_outcome(db, proposal_id, outcome)
        return outcome

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
    council = Council(genome, db)
    approved, transcript, vote_record = council.vote(council_proposal)

    # Record outcome
    outcome = {
        'proposal_id': proposal_id,
        'approved': approved,
        'fitness_score': fitness_score,
        'confidence': confidence,
        'transcript': transcript,
        'vote_record': vote_record,
        'timestamp': time.time()
    }

    if approved:
        try:
            _apply_proposal(db, agents, genome, ptype, changes, proposer_id)
            outcome['applied'] = True
            outcome['status'] = 'approved'
            logger.info(f"Proposal {proposal_id} approved and applied")
        except Exception as e:
            logger.error(f"Failed to apply proposal {proposal_id}: {e}")
            outcome['applied'] = False
            outcome['error'] = str(e)
            outcome['status'] = 'approval_failed'
    else:
        logger.info(f"Proposal {proposal_id} rejected")
        outcome['applied'] = False
        outcome['status'] = 'rejected'

    # Update proposal status
    db.update_properties(proposal_id, {'status': outcome['status']})

    _store_outcome(db, proposal_id, outcome)
    return outcome


def _store_outcome(db: HelixDBGit, proposal_id: str, outcome: Dict):
    """Store outcome as a node and link to proposal."""
    outcome_id = f"outcome_{int(time.time())}_{proposal_id[-8:]}"
    outcome['id'] = outcome_id
    outcome['type'] = 'ProposalOutcome'
    db.update_properties(outcome_id, outcome)
    # Link by reference (proposal_id field)
    logger.debug(f"Stored outcome {outcome_id} for proposal {proposal_id}")


def _apply_proposal(db: HelixDBGit, agents: List[Agent],
                    genome: Genome, ptype: str,
                    changes: Dict, proposer_id: Optional[str]):
    """Apply an approved proposal's changes."""
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
    elif ptype == 'model_proposal':
        handle_approved_model(changes, db, genome)
    elif ptype == 'user_product':
        handle_approved_user_request(changes, db, genome)  # to be implemented
    else:
        raise ProposalError(f"Unknown proposal type: {ptype}")


def _apply_genome_proposal(db: HelixDBGit, genome: Genome, changes: Dict):
    """Update genome parameters."""
    params = changes.get('parameters', {})
    for key, value in params.items():
        # Support nested updates (dot notation)
        keys = key.split('.')
        target = genome.data
        for k in keys[:-1]:
            target = target.setdefault(k, {})
        target[keys[-1]] = value
    logger.info(f"Genome updated: {params}")


def _apply_agent_proposal(db: HelixDBGit, agents: List[Agent], changes: Dict):
    """Modify an existing agent."""
    agent_id = changes.get('agent_id')
    if not agent_id:
        raise ProposalError("Agent proposal missing agent_id")

    # Find agent in list or load from DB
    agent = next((a for a in agents if a.agent_id == agent_id), None)
    if not agent:
        node = db.get_node(agent_id)
        if node:
            agent = Agent.from_dict(node, vectors={'leech': node.get('leech_vector')})
            agents.append(agent)
        else:
            raise ProposalError(f"Agent {agent_id} not found")

    if 'prompt' in changes:
        agent.prompt = changes['prompt']
    if 'traits' in changes:
        for key, val in changes['traits'].items():
            agent.traits[key] = max(0.0, min(1.0, val))
    agent.compute_state_vectors()
    agent.record_activity()
    agent.save_to_db(db)


def _apply_breed_proposal(db: HelixDBGit, agents: List[Agent],
                          genome: Genome, changes: Dict, proposer_id: Optional[str]):
    """Create a new agent by breeding two parents."""
    parent1_id = changes.get('parent1')
    parent2_id = changes.get('parent2')
    new_role = changes.get('new_role', 'hybrid')

    if not parent1_id or not parent2_id:
        raise ProposalError("Breed proposal missing parent IDs")

    parent1 = _find_agent(db, agents, parent1_id)
    parent2 = _find_agent(db, agents, parent2_id)

    phase = genome.data.get('helicity', {}).get('current_phase', 0)
    mutation_rate = genome.data.get('mutation', {}).get('base_rate', 0.1)
    bias = genome.data.get('helicity', {}).get('mutation_bias', 0.05)

    child = Agent.breed(parent1, parent2, new_role, mutation_rate, phase, bias)
    child.save_to_db(db)
    agents.append(child)
    logger.info(f"New agent bred: {child.agent_id}")


def _apply_merge_proposal(db: HelixDBGit, agents: List[Agent],
                          changes: Dict, proposer_id: Optional[str]):
    """Merge two agents into one (archive originals)."""
    agent1_id = changes.get('agent1')
    agent2_id = changes.get('agent2')
    new_role = changes.get('new_role', 'merged')

    if not agent1_id or not agent2_id:
        raise ProposalError("Merge proposal missing agent IDs")

    agent1 = _find_agent(db, agents, agent1_id)
    agent2 = _find_agent(db, agents, agent2_id)

    # Average traits
    new_traits = {}
    all_keys = set(agent1.traits.keys()) | set(agent2.traits.keys())
    for key in all_keys:
        v1 = agent1.traits.get(key, 0.5)
        v2 = agent2.traits.get(key, 0.5)
        new_traits[key] = (v1 + v2) / 2.0

    child = Agent(
        role=new_role,
        prompt=agent1.prompt,
        traits=new_traits,
        generation=max(agent1.generation, agent2.generation) + 1,
        parents=[agent1_id, agent2_id]
    )
    child.save_to_db(db)
    agents.append(child)

    # Archive originals (mark as inactive)
    agent1.epigenetic_marks['archived'] = {'value': True, 'decay': -1}  # permanent
    agent2.epigenetic_marks['archived'] = {'value': True, 'decay': -1}
    agent1.save_to_db(db)
    agent2.save_to_db(db)
    logger.info(f"Merged agents into {child.agent_id}")


def _apply_synthetic_proposal(db: HelixDBGit, agents: List[Agent],
                              changes: Dict, proposer_id: Optional[str]):
    """Create a new agent from a synthetic genome."""
    genome_data = changes.get('genome')
    if not genome_data:
        raise ProposalError("Synthetic agent proposal missing genome")

    role = genome_data.get('role', 'synthetic')
    prompt = genome_data.get('prompt', 'You are a synthetic agent.')
    traits = genome_data.get('traits', {})
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


def _find_agent(db: HelixDBGit, agents: List[Agent], agent_id: str) -> Agent:
    """Helper to find an agent in list or load from DB."""
    agent = next((a for a in agents if a.agent_id == agent_id), None)
    if not agent:
        node = db.get_node(agent_id)
        if node:
            agent = Agent.from_dict(node, vectors={'leech': node.get('leech_vector')})
            agents.append(agent)
        else:
            raise ProposalError(f"Agent {agent_id} not found")
    return agent
