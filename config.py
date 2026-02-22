"""
Configuration management for HelixHive Phase 2.
Loads the system configuration from a YAML file (separate from genome).
Config contains deployment‑specific settings (model endpoints, API keys, etc.)
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from copy import deepcopy

logger = logging.getLogger(__name__)

# Default configuration (can be overridden by config.yaml)
DEFAULT_CONFIG = {
    'model_providers': {
        'groq': {
            'base_url': 'https://api.groq.com/openai/v1',
            'default_model': 'llama3-8b-8192',
            'timeout': 30,
            'connection_pool_size': 10,
        },
        'openrouter': {
            'base_url': 'https://openrouter.ai/api/v1',
            'default_model': 'openrouter/auto',
            'timeout': 30,
            'connection_pool_size': 10,
        },
        'gemini': {
            'base_url': 'https://generativelanguage.googleapis.com',
            'default_model': 'gemini-2.0-flash',
            'timeout': 30,
            'connection_pool_size': 2,
        }
    },
    'rate_limits': {
        'default_rpm': 60,
        'default_tpm': 100000,
    },
    'circuit_breaker': {
        'failure_threshold': 5,
        'recovery_timeout': 60,
    },
    'cache': {
        'enabled': True,
        'max_size': 1000,
        'epsilon': 0.1,
    },
    'retry': {
        'max_retries': 5,
        'base_delay': 1.0,
        'max_delay': 3600.0,
    },
    'simulation': False,  # global simulation flag
}


class Config:
    """
    Thread‑safe configuration singleton.
    Loads from config.yaml (or custom path) and merges with defaults.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path: Optional[Path] = None):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True

        if config_path is None:
            # Look for config.yaml in the same directory as genome.yaml
            data_root = os.environ.get('HELIX_DATA_PATH')
            if data_root:
                config_path = Path(data_root) / 'config.yaml'
            else:
                config_path = Path('config.yaml')
        self.path = config_path

        self.data = DEFAULT_CONFIG.copy()
        self._load()

    def _load(self):
        """Load configuration from YAML if exists."""
        if self.path.exists():
            try:
                with open(self.path, 'r') as f:
                    loaded = yaml.safe_load(f)
                if loaded:
                    self.data = self._deep_merge(self.data, loaded)
                    logger.info(f"Config loaded from {self.path}")
                else:
                    logger.warning(f"Config file {self.path} is empty, using defaults")
            except Exception as e:
                logger.error(f"Failed to load config from {self.path}: {e}")
                logger.info("Using default config")
        else:
            logger.info(f"No config file at {self.path}, using defaults")

    def _deep_merge(self, base: Dict, overrides: Dict) -> Dict:
        result = deepcopy(base)
        for key, value in overrides.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = deepcopy(value)
        return result

    def save(self):
        """Save current config to YAML file (useful for exporting defaults)."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, 'w') as f:
                yaml.dump(self.data, f, default_flow_style=False, indent=2)
            logger.info(f"Config saved to {self.path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self.data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any):
        keys = key.split('.')
        target = self.data
        for k in keys[:-1]:
            if k not in target or not isinstance(target[k], dict):
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value

    def __getitem__(self, key):
        return self.data[key]

    def __contains__(self, key):
        return key in self.data


# Convenience function
def load_config() -> Config:
    """Return the config singleton."""
    return Config()
