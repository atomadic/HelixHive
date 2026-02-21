"""
Evo2-style fitness prediction for HelixHive Phase 2.
Predicts fitness of agents, proposals, and products using:
- Leech similarity to past successful items
- Novelty bonus
- Phase alignment
- Learned weights from historical outcomes (via world model)
All data is stored in the git‑backed database.
"""

import numpy as np
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from memory import HD, leech_encode, _LEECH_PROJ
from helixdb_git_adapter import HelixDBGit
from world_model import WorldModel

logger = logging.getLogger(__name__)


class FitnessPredictor:
    """
    Predicts fitness for HelixHive candidates using a combination of hand‑crafted and learned weights.
    """

    def __init__(self, db: HelixDBGit, genome: Any):
        self.db = db
        self.genome = genome
        # Load default weights from genome
        w = genome.data.get('evo2', {}).get('fitness_weights', {})
        self.alpha = w.get('leech_similarity', 0.5)
        self.beta = w.get('novelty_bonus', 0.3)
        self.gamma = w.get('phase_alignment', 0.2)
        self.current_phase = genome.data.get('helicity', {}).get('current_phase', 0)

        # Learned model
        self.world_model = WorldModel(db, genome)

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def predict(self, target_type: str, target_id: str,
                target_vector: Optional[np.ndarray] = None,
                context: Optional[Dict] = None) -> Tuple[float, float]:
        """
        Predict fitness for a target.
        Returns (fitness_score, confidence) both in [0,1].
        """
        if target_vector is None:
            target_vector = self._compute_vector(target_type, target_id, context)

        # Find similar items of the same type with fitness records
        similar = self._find_similar_with_fitness(target_type, target_vector, k=10)

        # Compute components
        sim_comp, sim_items = self._similarity_component(similar)
        novelty_comp = self._novelty_component(similar)
        phase_comp = self._phase_component(context)

        # Learned prediction
        learned, confidence = self.world_model.predict(target_type, target_vector, context)

        # Blend: use learned if confidence > 0.5, else hand‑crafted
        if confidence > 0.5:
            fitness = learned
        else:
            fitness = (self.alpha * sim_comp +
                       self.beta * novelty_comp +
                       self.gamma * phase_comp)

        # Confidence: based on number of similar items and world model confidence
        confidence = max(confidence, min(1.0, len(similar) / 10.0))

        self._store_fitness(target_type, target_id, fitness, confidence,
                            components={'sim': sim_comp, 'novelty': novelty_comp, 'phase': phase_comp},
                            similar_items=sim_items,
                            context=context)

        return fitness, confidence

    def record_outcome(self, target_type: str, target_id: str,
                       actual_fitness: float, context: Optional[Dict] = None):
        """Record actual outcome to update the world model."""
        self.world_model.add_training_example(target_type, target_id, actual_fitness, context)
        self._store_fitness(target_type, target_id, actual_fitness, 1.0,
                            record_type='outcome', context=context)
        logger.info(f"Recorded outcome for {target_type} {target_id}: {actual_fitness}")

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _compute_vector(self, target_type: str, target_id: str,
                        context: Optional[Dict]) -> np.ndarray:
        """Compute Leech vector for target based on its type."""
        if target_type == 'agent':
            node = self.db.get_node(target_id)
            if node and 'leech_vector' in node:
                return np.array(node['leech_vector'])
            raise ValueError(f"Agent {target_id} not found or missing Leech vector")
        elif target_type == 'proposal':
            proposer_id = context.get('proposer_id') if context else None
            if proposer_id:
                node = self.db.get_node(proposer_id)
                if node and 'leech_vector' in node:
                    return np.array(node['leech_vector'])
            # Fallback: compute from description
            desc = context.get('description', '')
            return self._text_to_leech(desc)
        elif target_type == 'product':
            text = context.get('text') if context else ''
            return self._text_to_leech(text)
        else:
            raise ValueError(f"Unknown target type: {target_type}")

    def _text_to_leech(self, text: str) -> np.ndarray:
        """Convert text to Leech vector."""
        words = text.split()[:200]
        if not words:
            return np.zeros(24, dtype=int)
        word_vecs = [HD.from_word(w) for w in words]
        hd_vec = HD.bundle(word_vecs)
        leech_float = np.dot(hd_vec.astype(np.float32), _LEECH_PROJ)
        return leech_encode(leech_float)

    def _find_similar_with_fitness(self, target_type: str, target_vec: np.ndarray,
                                   k: int = 10) -> List[Tuple[str, float, float]]:
        """Find nodes of target_type similar to target_vec that have fitness records."""
        # Get all nodes of target_type
        nodes = self.db.get_nodes_by_type(target_type)
        # Compute similarity (negative Euclidean distance for Leech vectors)
        similarities = []
        for node_id, node in nodes.items():
            vec = node.get('leech_vector')
            if vec is None:
                continue
            vec = np.array(vec)
            sim = -np.linalg.norm(target_vec - vec)  # negative distance
            # Get fitness records for this node
            fitness_records = self._get_fitness_records(node_id)
            if fitness_records:
                # Use most recent fitness
                latest = fitness_records[-1]
                similarities.append((node_id, sim, latest['fitness']))
        # Sort by similarity (higher is closer)
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:k]

    def _get_fitness_records(self, node_id: str) -> List[Dict]:
        """Retrieve fitness records associated with a node via HAS_FITNESS edges."""
        # In our current schema, FitnessRecord nodes have a target_id field.
        all_records = self.db.get_nodes_by_type('FitnessRecord')
        records = [r for r in all_records.values() if r.get('target_id') == node_id]
        records.sort(key=lambda x: x.get('timestamp', 0))
        return records

    def _store_fitness(self, target_type: str, target_id: str,
                       fitness: float, confidence: float,
                       components: Optional[Dict] = None,
                       similar_items: Optional[List] = None,
                       record_type: str = 'prediction',
                       context: Optional[Dict] = None) -> str:
        """Create a fitness record node."""
        record_id = f"fitness_{int(time.time())}_{target_id[-8:]}"
        record = {
            'id': record_id,
            'type': 'FitnessRecord',
            'target_type': target_type,
            'target_id': target_id,
            'fitness': fitness,
            'confidence': confidence,
            'components': components or {},
            'similar_items': similar_items or [],
            'record_type': record_type,
            'timestamp': datetime.now().timestamp(),
            'context': context or {}
        }
        self.db.update_properties(record_id, record)
        # Link by target_id (no edge needed)
        logger.debug(f"Stored fitness record {record_id}")
        return record_id

    def _similarity_component(self, similar: List[Tuple[str, float, float]]) -> Tuple[float, List]:
        """Compute weighted average fitness of similar items."""
        if not similar:
            return 0.5, []
        total_weight = 0.0
        weighted_sum = 0.0
        items = []
        for node_id, sim, fit in similar:
            weight = max(0.0, sim + 1)  # shift from [-1,1] to [0,2]
            weighted_sum += weight * fit
            total_weight += weight
            items.append({'node_id': node_id, 'similarity': sim, 'fitness': fit})
        if total_weight == 0:
            return 0.5, items
        return weighted_sum / total_weight, items

    def _novelty_component(self, similar: List[Tuple[str, float, float]]) -> float:
        """Novelty bonus: 1 - max similarity (clamped)."""
        if not similar:
            return 1.0
        max_sim = max(s for _, s, _ in similar)
        return max(0.0, 1.0 - max_sim)

    def _phase_component(self, context: Optional[Dict]) -> float:
        """Phase alignment: 1 if matches current phase, else 0.5."""
        if context and 'phase' in context:
            target_phase = context['phase']
            return 1.0 if target_phase == self.current_phase else 0.5
        return 1.0
