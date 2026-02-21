"""
Helical Phase Manager for HelixHive Phase 2.
Manages the binary helical phase (0=expansion, 1=refinement), triggers phase flip proposals,
and ensures flipped invariance by monitoring drift after flips.
Drift is measured using Leech‑grounded average trait vectors.
"""

import logging
import time
from typing import Dict, Any, Optional, List
import numpy as np

from agent import Agent
from helixdb_git_adapter import HelixDBGit
from memory import LeechErrorCorrector, leech_encode, _LEECH_PROJ, HD

logger = logging.getLogger(__name__)


class HelicalManager:
    """
    Manages helical phase transitions and invariance checks.
    """

    def __init__(self, db: HelixDBGit, genome: Any):
        self.db = db
        self.genome = genome

    # ----------------------------------------------------------------------
    # Phase flip proposal
    # ----------------------------------------------------------------------

    def check_flip(self, tick: int) -> Optional[Dict[str, Any]]:
        """
        Check if it's time to propose a phase flip based on flip_interval.
        Returns a proposal dict if flip should be proposed, else None.
        """
        helicity = self.genome.data.get('helicity', {})
        flip_interval = helicity.get('flip_interval', 50)
        last_flip = helicity.get('last_flip_tick', 0)

        if tick - last_flip >= flip_interval:
            current_phase = helicity.get('current_phase', 0)
            new_phase = 1 - current_phase
            proposal = {
                'type': 'phase_flip',
                'proposer_id': None,  # system-generated
                'description': f"Flip helical phase from {current_phase} to {new_phase}",
                'tags': ['helical', 'governance'],
                'changes': {
                    'new_phase': new_phase
                },
                'timestamp': time.time()
            }
            logger.info(f"Helical flip proposed at tick {tick}")
            return proposal
        return None

    # ----------------------------------------------------------------------
    # Execute flip (called when proposal approved)
    # ----------------------------------------------------------------------

    def execute_flip(self):
        """
        Execute a phase flip.
        Stores pre‑flip average trait vector (Leech‑grounded) for later invariance check.
        """
        helicity = self.genome.data.get('helicity', {})
        current = helicity.get('current_phase', 0)
        new_phase = 1 - current
        helicity['current_phase'] = new_phase
        helicity['last_flip_tick'] = self.genome.data.get('tick', 0)

        # Compute average trait vector before flip (using all agents)
        avg_traits = self._compute_average_traits()
        # Convert trait dict to Leech‑grounded vector for drift measurement
        if avg_traits:
            # Encode traits into a Leech vector (weighted combination of trait key vectors)
            trait_leech = self._traits_to_leech(avg_traits)
            helicity['avg_trait_before_flip'] = avg_traits
            helicity['avg_trait_leech_before'] = trait_leech.tolist()
        else:
            helicity['avg_trait_before_flip'] = {}
            helicity['avg_trait_leech_before'] = None

        helicity['invariance_check_pending'] = True
        self.genome.data['helicity'] = helicity
        logger.info(f"Helical phase flipped to {new_phase}")

    # ----------------------------------------------------------------------
    # Invariance check (call one tick after flip)
    # ----------------------------------------------------------------------

    def check_invariance(self, agents: List[Agent]) -> Optional[Dict[str, Any]]:
        """
        Check if post‑flip drift exceeds tolerance.
        Returns a repair proposal if needed, else None.
        Drift is measured as Leech distance between pre‑ and post‑flip average trait vectors.
        """
        helicity = self.genome.data.get('helicity', {})
        if not helicity.get('invariance_check_pending', False):
            return None

        # Compute current average traits
        current_avg = self._compute_average_traits_from_agents(agents)
        if not current_avg:
            helicity['invariance_check_pending'] = False
            return None

        # Get pre‑flip Leech vector
        pre_leech = helicity.get('avg_trait_leech_before')
        if pre_leech is None:
            helicity['invariance_check_pending'] = False
            return None
        pre_leech = np.array(pre_leech)

        # Compute current Leech vector from traits
        current_leech = self._traits_to_leech(current_avg)

        # Compute deviation (Euclidean distance in Leech space, but we use norm)
        deviation = np.linalg.norm(current_leech - pre_leech)

        # Apply Golay repair to ensure vectors are lattice points (they should be)
        corrected_pre, syn_pre = LeechErrorCorrector.correct(pre_leech)
        corrected_cur, syn_cur = LeechErrorCorrector.correct(current_leech)
        if syn_pre != 0 or syn_cur != 0:
            logger.warning("Invariance check: pre‑ or post‑flip vector not a lattice point; correcting.")
            deviation = np.linalg.norm(corrected_cur - corrected_pre)

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

    # ----------------------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------------------

    def _compute_average_traits(self) -> Dict[str, float]:
        """
        Compute average trait values across all agents in the database.
        Used before a flip.
        """
        agent_nodes = self.db.get_nodes_by_type('Agent')
        if not agent_nodes:
            return {}

        trait_sums = {}
        count = 0
        for node in agent_nodes.values():
            traits = node.get('traits', {})
            for k, v in traits.items():
                trait_sums[k] = trait_sums.get(k, 0) + v
            count += 1

        if count == 0:
            return {}
        avg = {k: v / count for k, v in trait_sums.items()}
        return avg

    def _compute_average_traits_from_agents(self, agents: List[Agent]) -> Dict[str, float]:
        """
        Compute average traits from a list of in‑memory Agent objects.
        """
        if not agents:
            return {}
        trait_sums = {}
        for agent in agents:
            for k, v in agent.traits.items():
                trait_sums[k] = trait_sums.get(k, 0) + v
        avg = {k: v / len(agents) for k, v in trait_sums.items()}
        return avg

    def _traits_to_leech(self, traits: Dict[str, float]) -> np.ndarray:
        """
        Convert a trait dictionary into a single Leech vector.
        Method: For each trait, get its word HD vector, weight by trait value,
        bundle, project to 24D, and encode to Leech lattice.
        """
        if not traits:
            return np.zeros(24, dtype=int)
        # Collect weighted HD vectors
        weighted_sum = None
        for key, val in traits.items():
            key_vec = HD.from_word(key).astype(np.float32)
            if weighted_sum is None:
                weighted_sum = val * key_vec
            else:
                weighted_sum += val * key_vec
        if weighted_sum is None:
            return np.zeros(24, dtype=int)
        # Quantize to bipolar? Not needed; we just need a vector for projection.
        # Project to 24D
        leech_float = np.dot(weighted_sum, _LEECH_PROJ)
        # Encode to Leech lattice
        leech_vec = leech_encode(leech_float)
        return leech_vec


# ----------------------------------------------------------------------
# Standalone functions for orchestrator
# ----------------------------------------------------------------------

def check_phase_flip(db: HelixDBGit, genome: Any, tick: int) -> Optional[Dict]:
    """Called at beginning of heartbeat to propose a phase flip if interval reached."""
    manager = HelicalManager(db, genome)
    return manager.check_flip(tick)


def execute_flip(db: HelixDBGit, genome: Any):
    """Called by proposals engine when a phase flip proposal is approved."""
    manager = HelicalManager(db, genome)
    manager.execute_flip()


def check_invariance(db: HelixDBGit, genome: Any, agents: List[Agent]) -> Optional[Dict]:
    """Called after a flip to check for drift; returns a repair proposal if needed."""
    manager = HelicalManager(db, genome)
    return manager.check_invariance(agents)
