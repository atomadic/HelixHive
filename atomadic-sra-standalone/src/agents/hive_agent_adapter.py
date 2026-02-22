"""
Hive Agent Adapter — Full HelixHive Agent ↔ SRA Luminary Bridge
SRA v3.3.0.0 | Expansion Cycle 4: HelixHive Fusion

Maps HelixHive Agent (Leech-encoded traits, mutation, breeding, fitness)
to SRA luminary system. Supports faction assignment, fitness tracking,
and Evo2 synthetic genome generation.

--- Helical Derivation (Rule 10) ---
Principle: Agent_traits ∈ [0,1]^5 → Leech_24D via RHC + HD projection
Derivation: HD = role_hd ⊕ Σ(trait_key ⊗ rhc_map(rhc_encode(v_i)))
Proof: Golay(24,12,8) guarantees d_min = 8 → 3-error correction
Audit: tau >= 0.9412, J >= 0.3, ΔM > 0
"""

import sys
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# Sovereign sys.path for HelixHive
_HIVE_ROOT = Path(__file__).resolve().parent.parent.parent / "HelixHive-main"
if _HIVE_ROOT.exists() and str(_HIVE_ROOT) not in sys.path:
    sys.path.insert(0, str(_HIVE_ROOT))

# Lazy imports
_Agent = None
_Evo2Generator = None
_fitness_mod = None
_imports_attempted = False


def _ensure_imports():
    """Attempt to import HelixHive agent-related classes."""
    global _Agent, _Evo2Generator, _fitness_mod, _imports_attempted
    if _imports_attempted:
        return _Agent is not None

    _imports_attempted = True

    try:
        from agent import Agent
        _Agent = Agent
        logger.info("[HiveAgentAdapter] ✓ HelixHive Agent class loaded")
    except Exception as e:
        logger.warning(f"[HiveAgentAdapter] ✗ Agent import failed: {e}")
        return False

    try:
        from evo2 import Evo2Generator
        _Evo2Generator = Evo2Generator
        logger.info("[HiveAgentAdapter] ✓ Evo2Generator loaded")
    except Exception as e:
        logger.debug(f"[HiveAgentAdapter] ✗ Evo2 not available: {e}")

    try:
        import fitness as fit_mod
        _fitness_mod = fit_mod
        logger.info("[HiveAgentAdapter] ✓ Fitness module loaded")
    except Exception as e:
        logger.debug(f"[HiveAgentAdapter] ✗ Fitness not available: {e}")

    return _Agent is not None


# ---- Default SRA trait mapping ----
SRA_DEFAULT_TRAITS = {
    "creativity": 0.7,
    "thoroughness": 0.8,
    "cooperativeness": 0.6,
    "ambition": 0.9,
    "curiosity": 0.85,
}


class HiveAgentAdapter:
    """
    Full adapter between HelixHive Agent and SRA luminary system.

    Capabilities:
    - Create, mutate, breed agents with Leech-encoded traits
    - Extract HD/E8/Leech vectors for pipeline consumption
    - Track fitness history per agent
    - Faction assignment support
    - Evo2 synthetic genome generation
    """

    def __init__(self):
        self.available = _ensure_imports()
        self._agents: Dict[str, Any] = {}  # id → Agent

    def create_agent(self, role: str, prompt: str,
                     traits: Optional[Dict[str, float]] = None,
                     agent_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Create a HelixHive Agent with SRA-compatible traits."""
        if not self.available:
            return None
        try:
            agent = _Agent(
                role=role, prompt=prompt,
                traits=traits or SRA_DEFAULT_TRAITS,
                agent_id=agent_id,
            )
            self._agents[agent.agent_id] = agent
            return self._agent_summary(agent)
        except Exception as e:
            logger.warning(f"[HiveAgentAdapter] create_agent failed: {e}")
            return None

    def mutate_agent(self, agent_id: str,
                     mutation_rate: float = 0.1,
                     phase: int = 0) -> Optional[Dict[str, Any]]:
        """Mutate agent traits with Gaussian noise."""
        if not self.available or agent_id not in self._agents:
            return None
        try:
            agent = self._agents[agent_id]
            agent.mutate(mutation_rate=mutation_rate, phase=phase)
            return self._agent_summary(agent, extra={"mutated": True})
        except Exception as e:
            logger.warning(f"[HiveAgentAdapter] mutate failed: {e}")
            return None

    def breed_agents(self, parent1_id: str, parent2_id: str,
                     new_role: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Breed two agents via crossover + mutation."""
        if not self.available:
            return None
        p1 = self._agents.get(parent1_id)
        p2 = self._agents.get(parent2_id)
        if p1 is None or p2 is None:
            logger.warning("[HiveAgentAdapter] One or both parents not found")
            return None
        try:
            child = _Agent.breed(p1, p2, new_role=new_role)
            self._agents[child.agent_id] = child
            return self._agent_summary(child, extra={
                "parents": [parent1_id, parent2_id],
                "bred": True,
            })
        except Exception as e:
            logger.warning(f"[HiveAgentAdapter] breed failed: {e}")
            return None

    def record_fitness(self, agent_id: str, fitness: float,
                       task_type: str = "general") -> Optional[Dict]:
        """Record a fitness score for an agent."""
        agent = self._agents.get(agent_id)
        if agent is None:
            return None
        try:
            import time
            entry = {"fitness": fitness, "task_type": task_type, "timestamp": time.time()}
            if not hasattr(agent, 'fitness_history'):
                agent.fitness_history = []
            agent.fitness_history.append(entry)
            return {"agent_id": agent_id, "fitness": fitness, "recorded": True}
        except Exception as e:
            logger.warning(f"[HiveAgentAdapter] record_fitness failed: {e}")
            return None

    def get_agent_fitness(self, agent_id: str) -> Optional[List[Dict]]:
        """Get fitness history for an agent."""
        agent = self._agents.get(agent_id)
        if agent is None:
            return None
        return getattr(agent, 'fitness_history', [])

    def assign_faction(self, agent_id: str, faction_id: int):
        """Assign a faction ID to an agent."""
        agent = self._agents.get(agent_id)
        if agent is not None:
            agent.faction_id = faction_id

    def get_leech_vector(self, agent_id: str) -> Optional[np.ndarray]:
        """Get the 24D Leech lattice vector for an agent."""
        agent = self._agents.get(agent_id)
        return agent.leech_vec if agent is not None else None

    def get_e8_vector(self, agent_id: str) -> Optional[np.ndarray]:
        """Get the 8D E8 lattice vector for an agent."""
        agent = self._agents.get(agent_id)
        return agent.e8_vec if agent is not None else None

    def get_hd_vector(self, agent_id: str) -> Optional[np.ndarray]:
        """Get the 10000D HD vector for an agent."""
        agent = self._agents.get(agent_id)
        return agent.hd_vec if agent is not None else None

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get full agent summary by ID."""
        agent = self._agents.get(agent_id)
        if agent is None:
            return None
        return self._agent_summary(agent)

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents managed by this adapter."""
        return [self._agent_summary(a) for a in self._agents.values()]

    def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent from the adapter."""
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False

    def _agent_summary(self, agent, extra: Optional[Dict] = None) -> Dict[str, Any]:
        """Build standardized summary dict for an agent."""
        summary = {
            "agent_id": agent.agent_id,
            "role": agent.role,
            "traits": dict(agent.traits),
            "generation": getattr(agent, 'generation', 0),
            "faction_id": getattr(agent, 'faction_id', None),
            "has_hd": agent.hd_vec is not None,
            "has_e8": agent.e8_vec is not None,
            "has_leech": agent.leech_vec is not None,
            "fitness_count": len(getattr(agent, 'fitness_history', [])),
        }
        if extra:
            summary.update(extra)
        return summary

    def get_state(self) -> Dict[str, Any]:
        """Diagnostic state."""
        return {
            "available": self.available,
            "agent_count": len(self._agents),
            "evo2_available": _Evo2Generator is not None,
            "fitness_available": _fitness_mod is not None,
        }
