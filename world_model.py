"""
World Model for HelixHive – learns to predict proposal outcomes and fitness from historical data.
Uses Bayesian linear regression (simple for Phase 1) and can be extended to more complex models.
"""

import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

import helixdb

logger = logging.getLogger(__name__)


class WorldModel:
    """
    Learns a mapping from feature vectors (derived from proposals/agents) to fitness scores.
    """

    def __init__(self, db: 'helixdb.HelixDB', genome: Any):
        self.db = db
        self.genome = genome
        self.model = None  # placeholder for learned model
        self.training_data = []  # list of (features, fitness)
        self._load_training_data()

    def _load_training_data(self):
        """Load historical FitnessRecord nodes with outcomes."""
        records = self.db.query_nodes_by_label('FitnessRecord')
        for rec in records:
            props = rec.properties
            if props.get('record_type') == 'outcome':
                # Need to extract features from the corresponding proposal/agent
                # For simplicity, we'll just store the target_id and later recompute features.
                # In a real system, we'd store features at prediction time.
                target_id = props.get('target_id')
                target_type = props.get('target_type')
                fitness = props.get('fitness')
                # We'll recompute features on the fly when training.
                self.training_data.append((target_type, target_id, fitness, props.get('context', {})))
        logger.info(f"Loaded {len(self.training_data)} training examples")

    def _extract_features(self, target_type: str, target_vector: np.ndarray,
                          context: Dict) -> np.ndarray:
        """
        Convert a target into a fixed‑length feature vector for the model.
        For now, just return the Leech vector (24D) as features.
        """
        # Ensure target_vector is a flat array of length 24 (Leech dimension)
        if target_vector.shape != (24,):
            # If not, maybe it's HD? For simplicity, assume it's already Leech.
            pass
        return target_vector.astype(np.float32).flatten()

    def train(self):
        """Train the model on collected data."""
        if len(self.training_data) < 10:
            logger.info("Not enough training data yet")
            return

        X = []
        y = []
        for target_type, target_id, fitness, context in self.training_data:
            # Retrieve the target's vector (we need to recompute or fetch from DB)
            # For simplicity, we assume we can get it from the target's node.
            node = self.db.get_node(target_id)
            if node and 'leech' in node.vectors:
                vec = node.vectors['leech']
                features = self._extract_features(target_type, vec, context)
                X.append(features)
                y.append(fitness)

        if len(X) < 10:
            return

        X = np.array(X)
        y = np.array(y)

        # Simple Bayesian linear regression
        # For Phase 1, we'll just do ordinary least squares with regularization.
        # Add bias term
        X = np.column_stack([X, np.ones(len(X))])
        # Ridge regression (L2)
        lambd = 1.0
        n_features = X.shape[1]
        I = np.eye(n_features)
        try:
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
        Returns (prediction, confidence).
        Confidence is based on number of training examples.
        """
        if self.model is None:
            return 0.5, 0.0

        features = self._extract_features(target_type, target_vector, context or {})
        # Add bias
        features = np.append(features, 1.0)
        pred = features @ self.model
        # Clamp to [0,1]
        pred = max(0.0, min(1.0, pred))
        confidence = min(1.0, len(self.training_data) / 100.0)
        return pred, confidence

    def add_training_example(self, target_type: str, target_id: str,
                             fitness: float, context: Optional[Dict]):
        """Add a new outcome to the training set."""
        self.training_data.append((target_type, target_id, fitness, context or {}))
        # Retrain if enough new data
        if len(self.training_data) % 10 == 0:
            self.train()
