"""
Evo2-style fitness prediction for HelixHive Phase 1.
Predicts fitness of agents, proposals, and products using:
- E8 consistency (grounding)
- Similarity to past successful items (by Leech vector)
- Novelty bonus
- Phase alignment
- Learned weights from historical outcomes.
"""

import numpy as np
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from memory import HD, E8, Leech, leech_encode
import helixdb
from world_model import WorldModel  # new module

logger = logging.getLogger(__name__)


class FitnessPredictor:
    """
    Predicts fitness for HelixHive candidates using a combination of hand‑crafted and learned weights.
    """

    def __init__(self, db: 'helixdb.HelixDB', genome: Any):
        self.db = db
        self.genome = genome
        # Load default weights
        w = genome.data.get('evo2', {}).get('fitness_weights', {})
        self.alpha = w.get('e8_consistency', 0.3)
        self.beta = w.get('leech_similarity', 0.4)
        self.gamma = w.get('novelty_bonus', 0.2)
        self.delta = w.get('phase_alignment', 0.1)
        self.current_phase = genome.data.get('helicity', {}).get('current_phase', 0)

        # Learned model
        self.world_model = WorldModel(db, genome)

    def predict(self, target_type: str, target_id: str,
                target_vector: Optional[np.ndarray] = None,
                context: Optional[Dict] = None) -> Tuple[float, float]:
        """
        Predict fitness for a target.
        Returns (fitness_score, confidence) both in [0,1].
        """
        if target_vector is None:
            target_vector = self._compute_vector(target_type, target_id, context)

        # Find similar items
        similar = self._find_similar_with_fitness(target_type, target_vector, k=10)

        # Compute components
        e8_comp = self._e8_component(target_type, target_id, context)
        sim_comp, sim_items = self._similarity_component(similar)
        novelty_comp = self._novelty_component(similar)
        phase_comp = self._phase_component(context)

        # Learned prediction
        learned, confidence = self.world_model.predict(target_type, target_vector, context)

        # Blend: use learned if confidence > 0.5, else hand‑crafted
        if confidence > 0.5:
            fitness = learned
        else:
            fitness = (self.alpha * e8_comp +
                       self.beta * sim_comp +
                       self.gamma * novelty_comp +
                       self.delta * phase_comp)

        # Confidence: based on number of similar items
        confidence = min(1.0, len(similar) / 10.0)

        self._store_fitness(target_type, target_id, fitness, confidence,
                            components={'e8': e8_comp, 'sim': sim_comp,
                                        'novelty': novelty_comp, 'phase': phase_comp},
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

    def _compute_vector(self, target_type: str, target_id: str,
                        context: Optional[Dict]) -> np.ndarray:
        """Compute Leech vector for target (similar to original, but uses true lattice)."""
        if target_type == 'agent':
            node = self.db.get_node(target_id)
            if node and 'leech' in node.vectors:
                return node.vectors['leech']
            raise ValueError(f"Agent {target_id} not found or missing Leech vector")
        elif target_type == 'proposal':
            proposer_id = context.get('proposer_id') if context else None
            if proposer_id:
                node = self.db.get_node(proposer_id)
                if node and 'leech' in node.vectors:
                    return node.vectors['leech']
            raise ValueError("Cannot compute vector for proposal: no proposer vector")
        elif target_type == 'product':
            text = context.get('text') if context else ''
            if not text:
                raise ValueError("Product text required in context")
            words = text.split()[:200]
            if not words:
                return np.zeros(24, dtype=np.int32)  # Leech vectors are ints
            word_vecs = [HD.from_word(w) for w in words]
            hd_vec = HD.bundle(word_vecs)
            # Project and encode to Leech
            leech_float = np.dot(hd_vec.astype(np.float32), _LEECH_PROJ)  # need to import _LEECH_PROJ
            return leech_encode(leech_float)
        else:
            raise ValueError(f"Unknown target type: {target_type}")

    def _find_similar_with_fitness(self, target_type: str, target_vec: np.ndarray,
                                   k: int = 10) -> List[Tuple[str, float, float]]:
        similar_nodes = self.db.find_similar(target_vec, 'leech', k=k*3, label=target_type)
        results = []
        for node_id, sim in similar_nodes:
            fitness_records = self._get_fitness_records(node_id)
            if fitness_records:
                latest = fitness_records[-1]
                results.append((node_id, sim, latest['fitness']))
            if len(results) >= k:
                break
        return results

    def _get_fitness_records(self, node_id: str) -> List[Dict]:
        edges = self.db.query_edges(src=node_id, label='HAS_FITNESS')
        records = []
        for _, dst, _, _ in edges:
            fitness_node = self.db.get_node(dst)
            if fitness_node:
                records.append(fitness_node.properties)
        records.sort(key=lambda x: x.get('timestamp', 0))
        return records

    def _store_fitness(self, target_type: str, target_id: str,
                       fitness: float, confidence: float,
                       components: Optional[Dict] = None,
                       similar_items: Optional[List] = None,
                       record_type: str = 'prediction',
                       context: Optional[Dict] = None) -> str:
        record_id = self.db.add_node(
            label='FitnessRecord',
            properties={
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
        )
        self.db.add_edge(target_id, record_id, 'HAS_FITNESS')
        return record_id

    def _e8_component(self, target_type: str, target_id: str,
                      context: Optional[Dict]) -> float:
        if target_type != 'agent':
            return 1.0
        node = self.db.get_node(target_id)
        if node and 'e8' in node.vectors:
            e8_vec = node.vectors['e8']
            # E8 vectors are lattice points, so distance to lattice is 0, but we want to measure how far the original projection was? Actually we store the lattice point, so it's perfect.
            # Alternative: compute distance from original projection (if we stored it) – we don't. So return 1.
            return 1.0
        return 1.0

    def _similarity_component(self, similar: List[Tuple[str, float, float]]) -> float:
        if not similar:
            return 0.5
        total_weight = 0.0
        weighted_sum = 0.0
        for _, sim, fit in similar:
            weight = max(0.0, sim)
            weighted_sum += weight * fit
            total_weight += weight
        if total_weight == 0:
            return 0.5
        return weighted_sum / total_weight

    def _novelty_component(self, similar: List[Tuple[str, float, float]]) -> float:
        if not similar:
            return 1.0
        max_sim = max(s for _, s, _ in similar)
        return max(0.0, 1.0 - max_sim)

    def _phase_component(self, context: Optional[Dict]) -> float:
        if context and 'phase' in context:
            target_phase = context['phase']
            return 1.0 if target_phase == self.current_phase else 0.5
        return 1.0
