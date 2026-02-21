"""
Continuous Golay self‑repair engine for HelixHive Phase 2.
Monitors all Leech vectors (agents, products, factions) and applies
syndrome‑based correction with epigenetic plasmid injection.
All changes are batched and committed atomically by the orchestrator.
"""

import numpy as np
import time
import hashlib
import logging
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path

from memory import LeechErrorCorrector, leech_encode
from helixdb_git_adapter import HelixDBGit  # will be defined later

logger = logging.getLogger(__name__)


class GolaySelfRepairEngine:
    """
    Autonomous self‑repair engine using Golay coset decoding.

    On each heartbeat, it scans all Leech‑encoded entities, computes syndromes,
    corrects any non‑zero vectors, and records epigenetic marks.
    """

    # Node types that carry Leech vectors and should be monitored.
    MONITORED_TYPES = ["Agent", "Product", "Faction", "Template", "Proposal"]

    def __init__(self, db: HelixDBGit, tick: int, config: Optional[Dict] = None):
        """
        Args:
            db: Git‑backed database adapter.
            tick: Current heartbeat tick (for deterministic plasmids).
            config: Optional configuration dict (e.g., plasmid strength).
        """
        self.db = db
        self.tick = tick
        self.config = config or {}
        self.plasmid_strength = self.config.get("plasmid_strength", 0.05)
        self.repair_count = 0
        self.syndrome_stats = {}

        # Verify coset table integrity on startup
        self._verify_coset_table()

    def _verify_coset_table(self):
        """Ensure the coset leader table is loadable and has correct shape."""
        try:
            LeechErrorCorrector._ensure_table()
            # Optionally compute a checksum (if stored with table)
            logger.info("Golay coset table verified.")
        except Exception as e:
            logger.error(f"Coset table verification failed: {e}")
            raise RuntimeError("Cannot start repair engine without valid coset table.")

    def _deterministic_plasmid(self, vector: np.ndarray, node_id: str) -> np.ndarray:
        """
        Generate an epigenetic plasmid as a small deterministic perturbation.
        The plasmid is a random vector within the Leech lattice's error‑correction radius,
        seeded by the node ID and current tick.
        Returns a vector that, when added to the original, stays within the Voronoi cell.
        """
        # Create a seed from node_id and tick
        seed_str = f"{node_id}:{self.tick}"
        seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
        rng = np.random.RandomState(seed)

        # Generate a small random perturbation (normal distribution scaled by strength)
        delta = rng.randn(24) * self.plasmid_strength
        # Add to original vector
        perturbed = vector + delta
        # Project back to nearest lattice point – this ensures the plasmid stays in the lattice
        corrected, _ = LeechErrorCorrector.correct(perturbed)
        return corrected

    def repair_vector(self, vector: np.ndarray, node_id: str, node_type: str) -> Tuple[np.ndarray, bool, int]:
        """
        Repair a single vector if needed.
        Returns (repaired_vector, was_repaired, syndrome).
        """
        corrected, syndrome = LeechErrorCorrector.correct(vector)
        if syndrome == 0:
            return vector, False, 0

        # Apply epigenetic plasmid (only if repair occurred)
        with_plasmid = self._deterministic_plasmid(corrected, node_id)
        self.repair_count += 1
        self.syndrome_stats[syndrome] = self.syndrome_stats.get(syndrome, 0) + 1
        logger.debug(f"Repaired {node_type} {node_id}: syndrome={syndrome}")
        return with_plasmid, True, syndrome

    def scan_and_repair(self) -> List[Tuple[str, str, np.ndarray]]:
        """
        Scan all monitored nodes and repair where needed.
        Returns list of (node_id, node_type, new_vector) for changed nodes.
        """
        changes = []
        self.repair_count = 0
        self.syndrome_stats.clear()

        for node_type in self.MONITORED_TYPES:
            nodes = self.db.get_nodes_by_type(node_type)  # returns dict node_id -> properties
            for node_id, node_data in nodes.items():
                leech_vec = node_data.get("leech_vector")
                if leech_vec is None:
                    continue
                # Ensure it's a numpy array
                if isinstance(leech_vec, list):
                    leech_vec = np.array(leech_vec, dtype=float)

                repaired, changed, syndrome = self.repair_vector(leech_vec, node_id, node_type)
                if changed:
                    changes.append((node_id, node_type, repaired))

        # Log summary
        if self.repair_count > 0:
            logger.info(f"Golay repair: {self.repair_count} vectors repaired. Syndromes: {self.syndrome_stats}")
        else:
            logger.debug("No repairs needed.")
        return changes

    def run_cycle(self) -> Dict[str, Any]:
        """
        Execute one full repair cycle and return metrics.
        Called by orchestrator during heartbeat.
        """
        start = time.time()
        changes = self.scan_and_repair()
        elapsed = time.time() - start

        # Update the database with changed vectors (but do not commit yet)
        for node_id, node_type, new_vec in changes:
            self.db.update_vector(node_id, node_type, "leech", new_vec.tolist())

        return {
            "vectors_scanned": sum(len(self.db.get_nodes_by_type(t)) for t in self.MONITORED_TYPES),
            "vectors_repaired": self.repair_count,
            "syndrome_stats": self.syndrome_stats.copy(),
            "elapsed_seconds": elapsed,
            "changes_pending": len(changes)
        }

    def self_test(self):
        """
        Run a quick fault‑injection test to verify repair capability.
        Raises AssertionError if test fails.
        """
        # Create a random lattice point
        test_vec = np.random.randn(24)
        lattice_point, _ = LeechErrorCorrector.correct(test_vec)
        # Introduce a small error (flip one coordinate)
        corrupted = lattice_point.copy()
        corrupted[0] += 2
        repaired, syndrome = LeechErrorCorrector.correct(corrupted)
        assert syndrome != 0, "Syndrome should be non‑zero after corruption"
        assert np.array_equal(repaired, lattice_point), "Repair failed to restore original"
        logger.info("Self‑test passed.")
