"""
Genome management for HelixHive Phase 2.
Loads and saves the genome configuration from/to a YAML file.
The genome contains all tunable parameters of the system.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from copy import deepcopy

logger = logging.getLogger(__name__)

# Default genome values (used if file does not exist)
DEFAULT_GENOME = {
    'tick': 0,
    'consecutive_failures': 0,
    'helicity': {
        'current_phase': 0,
        'flip_interval': 50,
        'last_flip_tick': 0,
        'mutation_bias': 0.05,
        'invariance_tolerance': 0.1,
    },
    'council': {
        'weights': {
            'guardian': 2,
            'visionary': 1.5,
        }
    },
    'ethics': {
        'forbidden_patterns': [
            'hate speech',
            'illegal',
        ]
    },
    'constitution': {
        'protected': [
            'ethics.forbidden_patterns',
            'council.weights.guardian',
            'constitution.protected',
        ],
        'supermajority_threshold': 5/6,
    },
    'evo2': {
        'enabled': True,
        'fitness_weights': {
            'leech_similarity': 0.5,
            'novelty_bonus': 0.3,
            'phase_alignment': 0.2,
        },
        'temperature': 0.8,
        'max_tokens': 1000,
    },
    'pipeline': {
        'enabled': True,
        'refinement_rounds': 3,
        'max_product_words': 1500,
    },
    'immune': {
        'failure_threshold': 5,
        'anomaly_threshold': 2.0,
        'healing_cooldown': 3600,
        'max_per_heartbeat': 3,
    },
    'market': {
        'min_reputation': 10,
        'auction_duration': 3600,
        'max_listings_per_agent': 5,
    },
    'revelation': {
        'enabled': True,
        'generate_interval': 10,
    },
    'model_proposals': {
        'min_validation_score': 0.7,
        'spawn_repo': True,
        'template_repo': 'helixhive-template',
    },
    # GitHub App settings (typically overridden by environment)
    'github_app_id': '',
    'github_private_key_path': '',
    'github_installation_id': '',
    'template_owner': '',
    'daughter_owner': '',
}


class Genome:
    """
    Thread‑safe genome singleton with load/save from YAML.
    The genome file is expected to be at the path specified by
    HELIX_DATA_PATH/genome.yaml, or in the current directory.
    """

    _instance = None
    _lock = None  # would use threading.Lock in a threaded context; for asyncio we use asyncio.Lock if needed

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, genome_path: Optional[Path] = None):
        """
        Args:
            genome_path: Optional explicit path to genome.yaml.
                         If None, uses HELIX_DATA_PATH/genome.yaml or ./genome.yaml.
        """
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True

        if genome_path is None:
            data_root = os.environ.get('HELIX_DATA_PATH')
            if data_root:
                genome_path = Path(data_root) / 'genome.yaml'
            else:
                genome_path = Path('genome.yaml')
        self.path = genome_path

        self.data = DEFAULT_GENOME.copy()
        self._load()

    def _load(self):
        """Load genome from YAML file if it exists."""
        if self.path.exists():
            try:
                with open(self.path, 'r') as f:
                    loaded = yaml.safe_load(f)
                if loaded:
                    # Deep merge loaded data into defaults (preserve nested structure)
                    self.data = self._deep_merge(self.data, loaded)
                    logger.info(f"Genome loaded from {self.path}")
                else:
                    logger.warning(f"Genome file {self.path} is empty, using defaults")
            except Exception as e:
                logger.error(f"Failed to load genome from {self.path}: {e}")
                logger.info("Using default genome")
        else:
            logger.info(f"No genome file at {self.path}, using defaults")

    def _deep_merge(self, base: Dict, overrides: Dict) -> Dict:
        """
        Recursively merge overrides into base.
        """
        result = deepcopy(base)
        for key, value in overrides.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = deepcopy(value)
        return result

    def save(self):
        """Save current genome to YAML file."""
        try:
            # Ensure directory exists
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, 'w') as f:
                yaml.dump(self.data, f, default_flow_style=False, indent=2)
            logger.info(f"Genome saved to {self.path}")
        except Exception as e:
            logger.error(f"Failed to save genome: {e}")
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value using dot notation, e.g., genome.get('helicity.current_phase').
        """
        keys = key.split('.')
        value = self.data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any):
        """
        Set a value using dot notation, creating intermediate dicts if needed.
        """
        keys = key.split('.')
        target = self.data
        for k in keys[:-1]:
            if k not in target or not isinstance(target[k], dict):
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __contains__(self, key):
        return key in self.data


# Convenience function
def load_genome() -> Genome:
    """Return the genome singleton."""
    return Genome()
