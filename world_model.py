"""
World Model for HelixHive Phase 2 – learns to predict fitness from historical outcomes.
Uses Bayesian linear regression with ridge regularization.
Features are Leech vectors (24D) plus bias.
"""

import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

from memory import leech_encode, _LEECH_PROJ, HD
from helixdb_git_adapter import HelixDBGit

logger = logging.getLogger(__name__)


class WorldModel:
    """
    Learns a mapping from Leech vectors to fitness scores using linear regression.
    Provides predictions with uncertainty (confidence based on training data size).
    """

    def __init__(self, db: HelixDBGit, genome: Any, max_examples: int = 1000):
        self.db = db
        self.genome = genome
        self.max_examples = max_examples
        self.model: Optional[np.ndarray] = None  # weights (including bias)
        self.training_data: List[Tuple[str, str, float, Dict]] = []  # (target_type, target_id, fitness, context)
        self._load_training_data()

    def _load_training_data(self):
        """Load historical FitnessRecord nodes with outcomes."""
        records = self.db.get_nodes_by_type('FitnessRecord')
        outcomes = [r for r in records.values() if r.get('record_type') == 'outcome']
        # Sort by timestamp and keep last max_examples
        outcomes.sort(key=lambda x: x.get('timestamp', 0))
        outcomes = outcomes[-self.max_examples:]
        for rec in outcomes:
            target_id = rec.get('target_id')
            target_type = rec.get('target_type')
            fitness = rec.get('fitness')
            context = rec.get('context', {})
            if target_id and target_type is not None and fitness is not None:
                self.training_data.append((target_type, target_id, fitness, context))
        logger.info(f"Loaded {len(self.training_data)} training examples")

    def _extract_features(self, target_type: str, target_vector: np.ndarray,
                          context: Dict) -> np.ndarray:
        """
        Convert a target into a feature vector.
        For now, use Leech vector (24D) plus bias.
        """
        # Ensure target_vector is a 24D float array
        if target_vector.shape != (24,):
            # If it's Leech integer, convert to float
            target_vector = target_vector.astype(np.float32)
        # Add bias term
        return np.append(target_vector, 1.0)

    def train(self):
        """Train the model on collected data."""
        if len(self.training_data) < 10:
            logger.info("Not enough training data yet")
            return

        X = []
        y = []
        for target_type, target_id, fitness, context in self.training_data:
            # Retrieve the target's Leech vector
            node = self.db.get_node(target_id)
            if node and 'leech_vector' in node:
                vec = np.array(node['leech_vector'])
                features = self._extract_features(target_type, vec, context)
                X.append(features)
                y.append(fitness)
            else:
                # If vector missing, skip
                logger.debug(f"Skipping training example {target_id}: no leech vector")

        if len(X) < 10:
            return

        X = np.array(X)
        y = np.array(y)

        # Ridge regression (L2 regularization)
        lambd = 1.0
        n_features = X.shape[1]
        I = np.eye(n_features)
        try:
            # (X^T X + λI)^{-1} X^T y
            theta = np.linalg.inv(X.T @ X + lambd * I) @ X.T @ y
        except np.linalg.LinAlgError:
            logger.warning("Training failed: singular matrix")
            return

        self.model = theta
        logger.info("World model trained")

    def predict(self, target_type: str, target_vector: np.ndarray,
                context: Optional[Dict]) -> Tuple[float, float]:
        """
        Predict fitness using the learned model.
        Returns (prediction, confidence) with confidence in [0,1].
        """
        if self.model is None:
            return 0.5, 0.0

        features = self._extract_features(target_type, target_vector, context or {})
        pred = features @ self.model
        # Clamp to [0,1]
        pred = max(0.0, min(1.0, pred))

        # Confidence based on number of training examples and recency (simple)
        confidence = min(1.0, len(self.training_data) / 100.0)
        return pred, confidence

    def add_training_example(self, target_type: str, target_id: str,
                             fitness: float, context: Optional[Dict]):
        """Add a new outcome to the training set."""
        self.training_data.append((target_type, target_id, fitness, context or {}))
        # Keep only last max_examples
        if len(self.training_data) > self.max_examples:
            self.training_data = self.training_data[-self.max_examples:]
        # Retrain if enough new data (every 10 examples)
        if len(self.training_data) % 10 == 0:
            self.train()

    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """Return feature weights for interpretability (if model trained)."""
        if self.model is None:
            return None
        # The last weight is bias; first 24 are Leech dimensions
        return {
            'leech_weights': self.model[:-1].tolist(),
            'bias': self.model[-1]
        }
