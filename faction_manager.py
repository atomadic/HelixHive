"""
Faction Manager for HelixHive Phase 2.

Detects emergent factions among agents via Leech vector clustering (DBSCAN).
Assigns each agent a faction ID, stores faction centroids in the database,
and provides methods to select the best creator for a given niche based on
faction expertise and Leech similarity.
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Set, Tuple
from collections import defaultdict
from sklearn.cluster import DBSCAN

from agent import Agent
from memory import HD, leech_encode, _LEECH_PROJ
from helixdb_git_adapter import HelixDBGit

logger = logging.getLogger(__name__)

# Constants for clustering
DEFAULT_EPS = 2.0           # Leech covering radius ~2
MIN_SAMPLES = 3              # Minimum agents to form a faction
CLUSTERING_INTERVAL = 10     # Re‑cluster every 10 ticks


class FactionManager:
    """
    Manages faction detection and assignment using Leech vectors.
    """

    def __init__(self, db: HelixDBGit):
        self.db = db
        self.agents: Dict[str, Agent] = {}          # agent_id -> Agent
        self.agent_vectors: Dict[str, np.ndarray] = {}  # agent_id -> Leech vector
        self.factions: Dict[int, Dict] = {}         # faction_id -> {"centroid": np.ndarray, "members": set}
        self.last_clustering_tick = -CLUSTERING_INTERVAL

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def load_agents(self, agent_list: List[Agent]):
        """Load agents into manager (called at heartbeat start)."""
        self.agents = {a.agent_id: a for a in agent_list}
        self.agent_vectors = {
            a.agent_id: a.leech_vec for a in agent_list if a.leech_vec is not None
        }

    def run_clustering_if_needed(self, current_tick: int) -> bool:
        """
        Run DBSCAN clustering if interval has passed.
        Returns True if factions changed.
        """
        if current_tick - self.last_clustering_tick < CLUSTERING_INTERVAL:
            return False
        return self.run_clustering()

    def run_clustering(self) -> bool:
        """
        Perform DBSCAN on current agent Leech vectors.
        Updates faction assignments and stores centroids.
        Returns True if factions changed.
        """
        if len(self.agent_vectors) < MIN_SAMPLES:
            logger.info("Not enough agents for clustering")
            return False

        # Prepare data matrix (N x 24)
        agent_ids = list(self.agent_vectors.keys())
        X = np.array([self.agent_vectors[aid] for aid in agent_ids], dtype=float)

        # DBSCAN
        clustering = DBSCAN(eps=DEFAULT_EPS, min_samples=MIN_SAMPLES, metric='euclidean').fit(X)
        labels = clustering.labels_

        # Build new factions
        new_factions: Dict[int, Dict] = {}
        for agent_id, label in zip(agent_ids, labels):
            if label == -1:
                continue  # noise, not assigned to any faction
            if label not in new_factions:
                new_factions[label] = {"members": set(), "centroid": None}
            new_factions[label]["members"].add(agent_id)

        # Compute centroids for each faction (Leech lattice point of mean)
        for label, faction in new_factions.items():
            member_vectors = [self.agent_vectors[aid] for aid in faction["members"]]
            mean_vec = np.mean(member_vectors, axis=0)
            # Encode to nearest Leech lattice point
            centroid = leech_encode(mean_vec)
            faction["centroid"] = centroid
            # Store in DB as Faction node
            self._store_faction(label, centroid, faction["members"])

        # Update assignments in agent objects
        for agent_id, label in zip(agent_ids, labels):
            agent = self.agents.get(agent_id)
            if agent:
                agent.faction_id = label if label != -1 else None

        self.factions = new_factions
        self.last_clustering_tick = self._get_current_tick()  # assume tick known
        logger.info(f"Clustering complete: {len(self.factions)} factions found")
        return True

    def select_best_creator(self, agents: List[Agent], niche: str) -> Agent:
        """
        Select the best agent to create a product for a given niche.
        Uses faction centroids and then similarity within the best faction.
        """
        if not agents:
            raise ValueError("No agents available")

        # If no factions yet, pick the agent with highest creativity
        if not self.factions:
            return max(agents, key=lambda a: a.traits.get("creativity", 0.5))

        # Compute niche Leech vector
        niche_vec = self._compute_niche_vector(niche)

        # Find faction whose centroid is closest to niche vector
        best_faction = None
        best_dist = float('inf')
        for fid, faction in self.factions.items():
            dist = np.linalg.norm(faction["centroid"] - niche_vec)
            if dist < best_dist:
                best_dist = dist
                best_faction = fid

        if best_faction is None:
            return agents[0]  # fallback

        # Within that faction, pick agent with highest creativity
        faction_members = [a for a in agents if getattr(a, 'faction_id', None) == best_faction]
        if not faction_members:
            return agents[0]  # fallback

        return max(faction_members, key=lambda a: a.traits.get("creativity", 0.5))

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _compute_niche_vector(self, niche: str) -> np.ndarray:
        """Convert niche string to Leech vector (bag‑of‑words + projection)."""
        words = niche.split()[:50]
        if not words:
            return np.zeros(24)
        word_vecs = [HD.from_word(w) for w in words]
        hd_vec = HD.bundle(word_vecs)
        leech_float = np.dot(hd_vec.astype(np.float32), _LEECH_PROJ)
        return leech_encode(leech_float)

    def _store_faction(self, faction_id: int, centroid: np.ndarray, member_ids: Set[str]):
        """Save faction info as a node in the database."""
        node_id = f"faction_{faction_id}_{int(time.time())}"
        node_data = {
            "id": node_id,
            "type": "Faction",
            "faction_id": int(faction_id),
            "centroid": centroid.tolist(),
            "member_count": len(member_ids),
            "members": list(member_ids),
            "created_at": time.time(),
        }
        self.db.update_properties(node_id, node_data)
        self.db.update_vector(node_id, "Faction", "leech", centroid)

    def _get_current_tick(self) -> int:
        """Retrieve current tick from genome (simplified)."""
        # In practice, the orchestrator passes tick; here we assume it's accessible.
        # For now, return a placeholder.
        return 0
