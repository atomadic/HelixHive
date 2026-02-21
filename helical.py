"""
Helical Phase Manager for HelixHive.
Manages the binary helical phase (0=expansion, 1=refinement), triggers phase flip proposals,
and ensures flipped invariance by monitoring drift after flips.
"""

import logging
import time
from typing import Dict, Any, Optional, List
import numpy as np

from agent import Agent
import helixdb

logger = logging.getLogger(__name__)


class HelicalManager:
    """
    Manages helical phase transitions and invariance checks.
    """

    def __init__(self, db: 'helixdb.HelixDB', genome: Any):
        self.db = db
        self.genome = genome

    def check_flip(self, tick: int) -> Optional[Dict[str, Any]]:
        """
        Check if it's time to propose a phase flip.
        Returns a proposal dict if flip should be proposed, else None.
        """
        helicity = self.genome.data.get('helicity', {})
        flip_interval = helicity.get('flip_interval', 50)
        last_flip = helicity.get('last_flip_tick', 0)

        if tick - last_flip >= flip_interval:
            # Generate flip proposal
            proposal = {
                'type': 'phase_flip',
                'proposer_id': None,  # system-generated
                'description': f"Flip helical phase from {helicity.get('current_phase', 0)} to {1 - helicity.get('current_phase', 0)}",
                'tags': ['helical', 'governance'],
                'changes': {},  # No changes to apply directly; council vote will trigger execute_flip
                'timestamp': time.time()
            }
            logger.info(f"Helical flip proposed at tick {tick}")
            return proposal
        return None

    def execute_flip(self):
        """
        Execute a phase flip (called when flip proposal is approved).
        Stores pre-flip average trait vector for later invariance check.
        """
        helicity = self.genome.data.get('helicity', {})
        current = helicity.get('current_phase', 0)
        new_phase = 1 - current
        helicity['current_phase'] = new_phase
        helicity['last_flip_tick'] = self.genome.data.get('tick', 0)

        # Compute average trait vector before flip (using current agents)
        avg_traits = self._compute_average_traits()
        helicity['avg_trait_before_flip'] = avg_traits
        helicity['invariance_check_pending'] = True

        self.genome.data['helicity'] = helicity
        logger.info(f"Helical phase flipped to {new_phase}")

    def check_invariance(self, agents: List[Agent]) -> Optional[Dict[str, Any]]:
        """
        Check if post-flip drift exceeds tolerance.
        Should be called one tick after a flip.
        Returns a repair proposal if needed, else None.
        """
        helicity = self.genome.data.get('helicity', {})
        if not helicity.get('invariance_check_pending', False):
            return None

        # Compute current average traits
        current_avg = self._compute_average_traits_from_agents(agents)
        before_avg = helicity.get('avg_trait_before_flip', {})

        # Compute deviation (simple Euclidean distance of trait vectors)
        if not before_avg or not current_avg:
            helicity['invariance_check_pending'] = False
            return None

        # Convert to arrays for comparison
        all_keys = set(before_avg.keys()) | set(current_avg.keys())
        vec_before = np.array([before_avg.get(k, 0.5) for k in sorted(all_keys)])
        vec_current = np.array([current_avg.get(k, 0.5) for k in sorted(all_keys)])
        deviation = np.linalg.norm(vec_before - vec_current)

        tolerance = helicity.get('invariance_tolerance', 0.1)
        if deviation > tolerance:
            logger.warning(f"Helical drift detected: deviation {deviation:.3f} > tolerance {tolerance}")
            # Generate repair proposal: reduce mutation bias
            current_bias = helicity.get('mutation_bias', 0.05)
            new_bias = current_bias * 0.9  # reduce by 10%
            proposal = {
                'type': 'genome',
                'proposer_id': None,
                'description': f"Reduce mutation bias due to helical drift (deviation {deviation:.3f})",
                'tags': ['helical', 'repair'],
                'changes': {
                    'parameters': {
                        'helicity.mutation_bias': new_bias
                    }
                },
                'timestamp': time.time()
            }
            helicity['invariance_check_pending'] = False
            return proposal
        else:
            logger.debug(f"Helical drift within tolerance: {deviation:.3f}")
            helicity['invariance_check_pending'] = False
            return None

    def _compute_average_traits(self) -> Dict[str, float]:
        """
        Compute average trait values across all agents in the database.
        Used before a flip.
        """
        # Query all agent nodes from DB
        agent_nodes = self.db.query_nodes_by_label('Agent')
        if not agent_nodes:
            return {}

        # Accumulate traits
        trait_sums = {}
        count = 0
        for node in agent_nodes:
            # Need to load full agent to get traits? We stored traits in properties.
            props = node.properties
            traits = props.get('traits', {})
            for k, v in traits.items():
                trait_sums[k] = trait_sums.get(k, 0) + v
            count += 1

        if count == 0:
            return {}

        avg = {k: v / count for k, v in trait_sums.items()}
        return avg

    def _compute_average_traits_from_agents(self, agents: List[Agent]) -> Dict[str, float]:
        """
        Compute average traits from a list of in-memory Agent objects.
        """
        if not agents:
            return {}

        trait_sums = {}
        for agent in agents:
            for k, v in agent.traits.items():
                trait_sums[k] = trait_sums.get(k, 0) + v

        avg = {k: v / len(agents) for k, v in trait_sums.items()}
        return avg


# Standalone functions for orchestrator to call

def check_phase_flip(db: 'helixdb.HelixDB', genome: Any, tick: int) -> Optional[Dict]:
    """
    Called at beginning of heartbeat to propose a phase flip if interval reached.
    Returns a proposal dict if flip should be proposed.
    """
    manager = HelicalManager(db, genome)
    return manager.check_flip(tick)


def maybe_execute_flip(db: 'helixdb.HelixDB', genome: Any, proposal: Dict):
    """
    Called by proposals engine when a phase flip proposal is approved.
    Executes the flip.
    """
    manager = HelicalManager(db, genome)
    manager.execute_flip()


def check_invariance(db: 'helixdb.HelixDB', genome: Any, agents: List[Agent]) -> Optional[Dict]:
    """
    Called after a flip to check for drift.
    Returns a repair proposal if needed.
    """
    manager = HelicalManager(db, genome)
    return manager.check_invariance(agents)
