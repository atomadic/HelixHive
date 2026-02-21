"""
Agent class for HelixHive Phase 2.

Represents an AI agent with:
- Traits (float values 0‑1) encoded via RHC and bound with role/trait keys.
- State vectors: HD (10k bipolar), E8 (8D lattice point), Leech (24D lattice point).
- Epigenetic marks for temporary modifications.
- Mitochondrial inheritance for specified traits.
"""

import uuid
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from memory import (
    HD, E8, LeechErrorCorrector,
    rhc_encode, rhc_bind, rhc_map_to_hd,
    e8_encode, leech_encode,
    _E8_PROJ, _LEECH_PROJ
)
from helixdb_git_adapter import HelixDBGit

logger = logging.getLogger(__name__)


class Agent:
    """
    An agent in the HelixHive community.
    """

    DEFAULT_TRAITS = {
        "creativity": 0.5,
        "thoroughness": 0.5,
        "cooperativeness": 0.5,
        "ambition": 0.5,
        "curiosity": 0.5
    }

    # Traits that are inherited only from the maternal parent (first parent in breed)
    MITOCHONDRIAL_TRAITS = ["cooperativeness", "ambition"]  # example

    # Cache for role HD vectors to avoid recomputation
    _role_hd_cache: Dict[str, np.ndarray] = {}

    def __init__(
        self,
        role: str,
        prompt: str,
        traits: Optional[Dict[str, float]] = None,
        agent_id: Optional[str] = None,
        generation: int = 0,
        parents: Optional[List[str]] = None,
        phase_history: Optional[List[int]] = None,
        reputation: int = 0,
        failures: int = 0,
        boost_remaining: float = 0.0,
        epigenetic_marks: Optional[Dict[str, Any]] = None,
        synthetic: bool = False,
        fitness_history: Optional[List[Dict]] = None,
        created_at: Optional[float] = None,
        last_active: Optional[float] = None,
        # Precomputed vectors (if loading from DB)
        hd_vec: Optional[np.ndarray] = None,
        e8_vec: Optional[np.ndarray] = None,
        leech_vec: Optional[np.ndarray] = None,
    ):
        self.agent_id = agent_id or str(uuid.uuid4())
        self.role = role
        self.prompt = prompt
        # Clamp traits to [0,1]
        self.traits = {}
        if traits:
            for k, v in traits.items():
                self.traits[k] = max(0.0, min(1.0, v))
        else:
            self.traits = self.DEFAULT_TRAITS.copy()
        self.generation = generation
        self.parents = parents if parents is not None else []
        self.phase_history = phase_history if phase_history is not None else []
        self.reputation = reputation
        self.failures = failures
        self.boost_remaining = boost_remaining
        self.epigenetic_marks = epigenetic_marks if epigenetic_marks is not None else {}
        self.synthetic = synthetic
        self.fitness_history = fitness_history if fitness_history is not None else []

        now = datetime.now().timestamp()
        self.created_at = created_at if created_at is not None else now
        self.last_active = last_active if last_active is not None else now

        # State vectors – use provided ones or compute
        self._hd_vec = hd_vec
        self._e8_vec = e8_vec
        self._leech_vec = leech_vec
        if self._hd_vec is None or self._e8_vec is None or self._leech_vec is None:
            self.compute_state_vectors()

    # ----------------------------------------------------------------------
    # State vector computation (using RHC and true lattices)
    # ----------------------------------------------------------------------

    @classmethod
    def _get_role_hd(cls, role: str) -> np.ndarray:
        """Cached role HD vector."""
        if role not in cls._role_hd_cache:
            cls._role_hd_cache[role] = HD.from_word(role)
        return cls._role_hd_cache[role]

    def compute_state_vectors(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute HD, E8, and Leech state vectors:
        - HD: role vector ⊕ [trait_key ⊗ rhc_map_to_hd(rhc_encode(trait_value))] for each trait.
        - E8: project HD to 8D, then encode to nearest E8 lattice point.
        - Leech: project HD to 24D, then encode to nearest Leech lattice point.
        """
        # Role vector (cached)
        role_vec = self._get_role_hd(self.role)

        # For each trait, generate vector = trait_key ⊗ (RHC value mapped to HD)
        trait_vectors = []
        for key, val in self.traits.items():
            if val == 0:
                continue
            key_vec = HD.from_word(key)                     # bipolar HD
            val_rhc = rhc_encode(val)                       # bipolar RHC vector
            val_hd = rhc_map_to_hd(val_rhc)                 # now length HD_DIM
            # Bind key and value
            combined = HD.bind(key_vec, val_hd)
            trait_vectors.append(combined)

        # Bundle all trait vectors with the role vector
        all_vectors = [role_vec] + trait_vectors
        self._hd_vec = HD.bundle(all_vectors)

        # E8: project to 8D and encode
        e8_float = np.dot(self._hd_vec.astype(np.float32), _E8_PROJ)
        self._e8_vec = e8_encode(e8_float)

        # Leech: project to 24D and encode
        leech_float = np.dot(self._hd_vec.astype(np.float32), _LEECH_PROJ)
        self._leech_vec = leech_encode(leech_float)

        return self._hd_vec, self._e8_vec, self._leech_vec

    @property
    def hd_vec(self) -> np.ndarray:
        if self._hd_vec is None:
            self.compute_state_vectors()
        return self._hd_vec

    @property
    def e8_vec(self) -> np.ndarray:
        if self._e8_vec is None:
            self.compute_state_vectors()
        return self._e8_vec

    @property
    def leech_vec(self) -> np.ndarray:
        if self._leech_vec is None:
            self.compute_state_vectors()
        return self._leech_vec

    # ----------------------------------------------------------------------
    # Epigenetic marks (temporary modifications)
    # ----------------------------------------------------------------------

    def apply_epigenetic_decay(self):
        """Decrement decay counters and remove expired marks."""
        expired = []
        for key, mark in self.epigenetic_marks.items():
            if 'decay' in mark:
                mark['decay'] -= 1
                if mark['decay'] <= 0:
                    expired.append(key)
        for key in expired:
            del self.epigenetic_marks[key]

    def add_epigenetic_mark(self, key: str, value: Any, decay: int = 10):
        """Add a temporary mark that decays after `decay` ticks."""
        self.epigenetic_marks[key] = {'value': value, 'decay': decay}

    # ----------------------------------------------------------------------
    # Mutation and breeding (enhanced)
    # ----------------------------------------------------------------------

    def mutate(self, mutation_rate: float = 0.1, phase: int = 0, bias: float = 0.05):
        """
        Mutate traits with Gaussian noise. Phase determines bias direction.
        Epigenetic marks may temporarily modify mutation effect.
        """
        # Check for epigenetic modifiers (e.g., "cautious" reduces mutation)
        cautious = self.epigenetic_marks.get('cautious', {}).get('value', 1.0)
        effective_rate = mutation_rate * cautious

        for key in self.traits:
            delta = np.random.normal(0, effective_rate)
            if phase == 0:
                delta += bias
            else:
                delta -= bias
            self.traits[key] = np.clip(self.traits[key] + delta, 0.0, 1.0)

        # Apply epigenetic decay
        self.apply_epigenetic_decay()

        # Recompute vectors
        self.compute_state_vectors()
        self.last_active = datetime.now().timestamp()

    @classmethod
    def breed(cls, parent1: 'Agent', parent2: 'Agent', new_role: Optional[str] = None,
              mutation_rate: float = 0.1, phase: int = 0, bias: float = 0.05) -> 'Agent':
        """
        Create a new agent by combining traits from two parents.
        - For most traits: randomly choose from either parent (crossover).
        - Mitochondrial traits: inherit only from first parent (maternal).
        - Prompt: combine both prompts using a template.
        """
        if new_role is None:
            new_role = f"{parent1.role}_{parent2.role}_hybrid"

        # Crossover for non‑mitochondrial traits
        all_keys = set(parent1.traits.keys()) | set(parent2.traits.keys())
        new_traits = {}
        for key in all_keys:
            if key in cls.MITOCHONDRIAL_TRAITS:
                # Inherit from parent1 (maternal)
                new_traits[key] = parent1.traits.get(key, 0.5)
            else:
                # Random choice
                if np.random.rand() < 0.5:
                    new_traits[key] = parent1.traits.get(key, 0.5)
                else:
                    new_traits[key] = parent2.traits.get(key, 0.5)

        # Combine prompts (simple concatenation)
        new_prompt = f"You are a blend of {parent1.role} and {parent2.role}.\n\n{parent1.prompt}\n\n{parent2.prompt}"

        child = cls(
            role=new_role,
            prompt=new_prompt,
            traits=new_traits,
            generation=max(parent1.generation, parent2.generation) + 1,
            parents=[parent1.agent_id, parent2.agent_id],
            synthetic=False
        )
        child.mutate(mutation_rate, phase, bias)
        return child

    # ----------------------------------------------------------------------
    # Serialization and DB integration
    # ----------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return JSON‑serializable dictionary (without vectors)."""
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "prompt": self.prompt,
            "traits": self.traits,
            "generation": self.generation,
            "parents": self.parents,
            "phase_history": self.phase_history,
            "reputation": self.reputation,
            "failures": self.failures,
            "boost_remaining": self.boost_remaining,
            "epigenetic_marks": self.epigenetic_marks,
            "synthetic": self.synthetic,
            "fitness_history": self.fitness_history,
            "created_at": self.created_at,
            "last_active": self.last_active,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], vectors: Optional[Dict[str, np.ndarray]] = None) -> 'Agent':
        """
        Reconstruct agent from dictionary and optional vectors.
        If vectors not provided, they will be recomputed.
        """
        # Extract vectors if present
        hd_vec = vectors.get('hd') if vectors else None
        e8_vec = vectors.get('e8') if vectors else None
        leech_vec = vectors.get('leech') if vectors else None

        # Convert list back to numpy if needed
        if hd_vec is not None and isinstance(hd_vec, list):
            hd_vec = np.array(hd_vec, dtype=np.int8)
        if e8_vec is not None and isinstance(e8_vec, list):
            e8_vec = np.array(e8_vec, dtype=np.int8)  # E8 can be int or half‑int; store as float?
            # Actually E8 lattice points are int or half‑int; we store as float to preserve half.
        if leech_vec is not None and isinstance(leech_vec, list):
            leech_vec = np.array(leech_vec, dtype=int)  # Leech vectors are integers

        return cls(
            role=data["role"],
            prompt=data["prompt"],
            traits=data.get("traits"),
            agent_id=data["agent_id"],
            generation=data.get("generation", 0),
            parents=data.get("parents", []),
            phase_history=data.get("phase_history", []),
            reputation=data.get("reputation", 0),
            failures=data.get("failures", 0),
            boost_remaining=data.get("boost_remaining", 0.0),
            epigenetic_marks=data.get("epigenetic_marks", {}),
            synthetic=data.get("synthetic", False),
            fitness_history=data.get("fitness_history", []),
            created_at=data.get("created_at"),
            last_active=data.get("last_active"),
            hd_vec=hd_vec,
            e8_vec=e8_vec,
            leech_vec=leech_vec,
        )

    def save_to_db(self, db: HelixDBGit):
        """
        Save agent to the database (properties and vectors).
        """
        # Save properties (JSON)
        db.update_properties(self.agent_id, self.to_dict())

        # Save vectors (as numpy arrays)
        db.update_vector(self.agent_id, "Agent", "hd", self.hd_vec)
        db.update_vector(self.agent_id, "Agent", "e8", self.e8_vec)
        db.update_vector(self.agent_id, "Agent", "leech", self.leech_vec)

    @classmethod
    def load_from_db(cls, db: HelixDBGit, agent_id: str) -> Optional['Agent']:
        """
        Load agent from database by ID.
        """
        node = db.get_node(agent_id)
        if not node:
            return None
        # The node dict already contains "leech_vector" etc. if they were loaded.
        # We need to extract properties (without vectors) and vectors separately.
        props = {k: v for k, v in node.items() if k not in ('leech_vector', 'hd_vector', 'e8_vector')}
        vectors = {}
        if 'hd_vector' in node:
            vectors['hd'] = node['hd_vector']
        if 'e8_vector' in node:
            vectors['e8'] = node['e8_vector']
        if 'leech_vector' in node:
            vectors['leech'] = node['leech_vector']
        return cls.from_dict(props, vectors)

    # ----------------------------------------------------------------------
    # Utility
    # ----------------------------------------------------------------------

    def add_fitness_record(self, fitness: float, context: str):
        self.fitness_history.append({
            "timestamp": datetime.now().timestamp(),
            "fitness": fitness,
            "context": context
        })
        if len(self.fitness_history) > 100:
            self.fitness_history = self.fitness_history[-100:]

    def record_activity(self):
        self.last_active = datetime.now().timestamp()

    def __repr__(self):
        return f"Agent(role={self.role}, id={self.agent_id[:8]})”
