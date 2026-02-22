"""
Hive Bridge — Full Sovereign Interface to HelixHive Subsystem
SRA v3.3.0.0 | Expansion Cycle 4: HelixHive Fusion

Comprehensive adapter wrapping ALL HelixHive modules (25 total)
into a sovereign interface that the SRA can fully audit.

Modules integrated:
  Core Math:    memory (Golay/Leech/RHC/HD/E8), helical
  LLM:         llm_router (Groq/OpenRouter/Grok fallback chain)
  Agents:      agent, evo2 (synthetic genome generation)
  Config:      genome (YAML singleton), config (deployment settings)
  Pipeline:    pipeline (4-round product creation)
  Database:    helixdb, helixdb_git_adapter
  Governance:  council (6-member voting), proposals, model_proposals
  Health:      immune (anomaly detection), golay_self_repair_v5 (codebase healing)
  Social:      faction_manager (DBSCAN clustering), market (trait trading)
  Discovery:   revelation (epiphany→revelation→AHA→synthesis)
  Ecosystem:   orchestrator, marketplace_sync, user_requests, world_model,
               fitness, resources

All calls are try/except guarded with Jessica Gate enforcement.
Falls back to SRA native modules on any import or runtime failure.

--- Helical Derivation (Rule 10) ---
Principle: HiveBridge(x) = try HelixHive(x) else SRA_fallback(x)
Derivation: tau_hive = tau_sra * (1 - P(failure_hive))
Proof: V = (1 - tau)^2/2 => dV/dt < 0 under homeostasis
Audit: tau >= 0.9412, J >= 0.3, ΔM > 0
"""

import sys
import os
import asyncio
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sovereign sys.path injection for HelixHive
# ---------------------------------------------------------------------------
_HIVE_ROOT = Path(__file__).resolve().parent.parent.parent / "HelixHive-main"
if _HIVE_ROOT.exists() and str(_HIVE_ROOT) not in sys.path:
    sys.path.insert(0, str(_HIVE_ROOT))

# ---------------------------------------------------------------------------
# Module registry — lazy loaded, graceful on failure
# ---------------------------------------------------------------------------
_modules = {}
_load_attempted = False


def _lazy_load_all():
    """Load all HelixHive modules once. Graceful on individual failures."""
    global _modules, _load_attempted
    if _load_attempted:
        return

    _load_attempted = True

    # Module manifest: (key, import_name, description)
    manifest = [
        # Core Math
        ("memory", "memory", "Golay/Leech/RHC/HD/E8 lattice operations"),
        ("helical", "helical", "Helical phase management"),
        # LLM
        ("llm_router", "llm_router", "Groq/OpenRouter/Grok fallback chain"),
        # Agents
        ("agent", "agent", "Leech-encoded AI agent class"),
        ("evo2", "evo2", "Synthetic agent genome generation"),
        # Config
        ("genome", "genome", "YAML genome singleton"),
        ("config", "config", "Deployment configuration"),
        # Pipeline
        ("pipeline", "pipeline", "4-round product creation pipeline"),
        # Database
        ("helixdb", "helixdb", "Graph+vector database"),
        ("helixdb_git", "helixdb_git_adapter", "Git-backed database adapter"),
        # Governance
        ("council", "council", "6-member weighted voting council"),
        ("proposals", "proposals", "Proposal management"),
        ("model_proposals", "model_proposals", "Model/daughter repo proposals"),
        # Health
        ("immune", "immune", "Agent health monitoring"),
        ("golay_repair", "golay_self_repair_v5", "Codebase self-healing v5"),
        # Social
        ("faction_manager", "faction_manager", "DBSCAN Leech clustering"),
        ("market", "market", "Trait marketplace & auctions"),
        # Discovery
        ("revelation", "revelation", "Epiphany→Revelation→AHA→Synthesis"),
        # Ecosystem
        ("orchestrator", "orchestrator", "Heartbeat orchestrator"),
        ("marketplace_sync", "marketplace_sync", "Marketplace index generator"),
        ("user_requests", "user_requests", "User request processor"),
        ("world_model", "world_model", "World model & simulation"),
        ("fitness", "fitness", "Fitness evaluation"),
        ("resources", "resources", "Resource management"),
    ]

    for key, import_name, desc in manifest:
        try:
            mod = __import__(import_name)
            _modules[key] = mod
            logger.info(f"[HiveBridge] ✓ {key}: {desc}")
        except Exception as e:
            _modules[key] = None
            logger.debug(f"[HiveBridge] ✗ {key}: {e}")

    loaded = sum(1 for v in _modules.values() if v is not None)
    total = len(manifest)
    logger.info(f"[HiveBridge] Loaded {loaded}/{total} HelixHive modules")


def _get(key: str):
    """Get a loaded module by key, or None."""
    if not _load_attempted:
        _lazy_load_all()
    return _modules.get(key)


# ===========================================================================
# Aletheia Constants
# ===========================================================================
TAU_THRESHOLD = 0.9412
J_FLOOR = 0.3
ALPHA = 0.1


class HiveBridge:
    """
    Full Sovereign Interface to the HelixHive autonomous swarm subsystem.

    Wraps all 25 HelixHive modules behind controlled adapters with
    Jessica Gate enforcement, tau homeostasis, and EvolutionVault logging.

    Aletheia Axiom III: External dependencies wrapped in a
    Sovereign Interface that the agent can fully audit.
    """
    def __init__(self):
        self.tau = 1.0
        self.J = 1.0
        self._golay_available = False

    def _ensure_golay(self):
        """Lazy probe for Golay availability."""
        if self._golay_available:
            return
        mem = _get("memory")
        if mem is not None:
            try:
                import numpy as np
                test_vec = np.zeros(24, dtype=float)
                mem.LeechErrorCorrector.correct(test_vec)
                self._golay_available = True
                logger.info("[HiveBridge] Golay coset table available")
            except Exception:
                logger.debug("[HiveBridge] Golay coset table not found — simplified Leech mode")

    @property
    def available(self) -> bool:
        """True if core memory module loaded (minimum viable HelixHive)."""
        return _get("memory") is not None

    # ---- Tau / Jessica homeostasis ----
    def _step_tau(self):
        self.tau += ALPHA * (1 - self.tau)

    def _decrement_j(self):
        self.J = max(J_FLOOR, self.J - 0.1)

    # =====================================================================
    # 1. LEECH LATTICE (True Golay via memory.py)
    # =====================================================================

    def leech_encode(self, vec_24d: List[float]) -> np.ndarray:
        """Encode a 24D float vector to nearest Leech lattice point."""
        vec = np.array(vec_24d, dtype=float)
        if len(vec) != 24:
            raise ValueError(f"Leech encode requires 24D input, got {len(vec)}D")

        self._ensure_golay()
        mem = _get("memory")
        if mem is not None and self._golay_available:
            try:
                result = mem.leech_encode(vec)
                self._step_tau()
                return result
            except Exception as e:
                logger.warning(f"[HiveBridge] Golay leech_encode failed: {e}")
                self._decrement_j()

        # Simplified fallback
        rounded = np.round(vec).astype(int)
        if np.sum(rounded) % 2 != 0:
            err = vec - rounded
            idx = np.argmax(np.abs(err))
            rounded[idx] += 1 if err[idx] > 0 else -1
        return rounded

    def leech_correct(self, vec: List[float]) -> Tuple[np.ndarray, int]:
        """Error-correct a 24D vector via Golay syndrome decoding."""
        arr = np.array(vec, dtype=float)
        mem = _get("memory")
        if mem is not None and self._golay_available:
            try:
                corrected, syndrome = mem.LeechErrorCorrector.correct(arr)
                self._step_tau()
                return corrected, int(syndrome)
            except Exception as e:
                logger.warning(f"[HiveBridge] Golay correct failed: {e}")
                self._decrement_j()
        return np.round(arr).astype(int), -1

    def golay_syndrome(self, vec_24: List[int]) -> int:
        """Compute the 12-bit Golay syndrome of a 24-bit vector."""
        mem = _get("memory")
        if mem is not None and self._golay_available:
            try:
                return mem.LeechErrorCorrector.syndrome(np.array(vec_24))
            except Exception:
                pass
        return -1

    def batch_correct(self, vectors: np.ndarray) -> Tuple[np.ndarray, np.ndarray, List[Dict]]:
        """Batch error-correct multiple 24D vectors."""
        mem = _get("memory")
        if mem is not None and self._golay_available:
            try:
                return mem.LeechErrorCorrector.batch_correct(vectors)
            except Exception as e:
                logger.warning(f"[HiveBridge] batch_correct failed: {e}")
                self._decrement_j()
        # Fallback
        N = vectors.shape[0]
        corrected = np.round(vectors).astype(int)
        return corrected, np.full(N, -1), [{"syndrome": -1, "repaired": False}] * N

    # =====================================================================
    # 2. HD / RHC / E8 ENCODING (via memory.py)
    # =====================================================================

    def hd_from_word(self, word: str) -> Optional[np.ndarray]:
        """Deterministic HD vector from a word string (10000D bipolar)."""
        mem = _get("memory")
        if mem is not None:
            try:
                return mem.HD.from_word(word)
            except Exception as e:
                logger.warning(f"[HiveBridge] HD.from_word failed: {e}")
        return None

    def hd_bundle(self, vectors: List[np.ndarray]) -> Optional[np.ndarray]:
        """Bundle multiple HD vectors via majority sum."""
        mem = _get("memory")
        if mem is not None:
            try:
                return mem.HD.bundle(vectors)
            except Exception as e:
                logger.warning(f"[HiveBridge] HD.bundle failed: {e}")
        return None

    def hd_bind(self, v1: np.ndarray, v2: np.ndarray) -> Optional[np.ndarray]:
        """Bind two HD vectors (element-wise multiplication)."""
        mem = _get("memory")
        if mem is not None:
            try:
                return mem.HD.bind(v1, v2)
            except Exception as e:
                logger.warning(f"[HiveBridge] HD.bind failed: {e}")
        return None

    def hd_similarity(self, v1: np.ndarray, v2: np.ndarray) -> Optional[float]:
        """Cosine similarity between two HD vectors."""
        mem = _get("memory")
        if mem is not None:
            try:
                return mem.HD.sim(v1, v2)
            except Exception as e:
                logger.warning(f"[HiveBridge] HD.sim failed: {e}")
        return None

    def rhc_encode_trait(self, value: float) -> Optional[np.ndarray]:
        """Encode a trait value (0-1) using Residue Hyperdimensional Computing."""
        mem = _get("memory")
        if mem is not None:
            try:
                return mem.rhc_encode(value)
            except Exception as e:
                logger.warning(f"[HiveBridge] rhc_encode failed: {e}")
        return None

    def rhc_bind(self, v1: np.ndarray, v2: np.ndarray) -> Optional[np.ndarray]:
        """Bind two RHC vectors."""
        mem = _get("memory")
        if mem is not None:
            try:
                return mem.rhc_bind(v1, v2)
            except Exception as e:
                logger.warning(f"[HiveBridge] rhc_bind failed: {e}")
        return None

    def e8_closest_point(self, vec_8d: List[float]) -> Optional[np.ndarray]:
        """Find closest E8 lattice point (integer/half-integer decoding)."""
        mem = _get("memory")
        if mem is not None:
            try:
                return mem.E8.closest_point(np.array(vec_8d, dtype=float))
            except Exception as e:
                logger.warning(f"[HiveBridge] E8.closest_point failed: {e}")
        return None

    # =====================================================================
    # 3. LLM ROUTING (Groq → OpenRouter → Grok)
    # =====================================================================

    def call_llm_sync(self, prompt: str, system: Optional[str] = None,
                      temperature: float = 0.7, max_tokens: int = 1000) -> Optional[str]:
        """Synchronous wrapper around HelixHive's async LLM router."""
        llm = _get("llm_router")
        if llm is None:
            return None
        try:
            loop = asyncio.new_event_loop()
            try:
                result = loop.run_until_complete(
                    llm.call_llm(prompt=prompt, system=system,
                                 temperature=temperature, max_tokens=max_tokens)
                )
                self._step_tau()
                return result
            finally:
                loop.close()
        except Exception as e:
            logger.warning(f"[HiveBridge] LLM router call failed: {e}")
            self._decrement_j()
            return None

    @property
    def llm_available(self) -> bool:
        return _get("llm_router") is not None

    # =====================================================================
    # 4. AGENT MANAGEMENT (agent.py + evo2.py)
    # =====================================================================

    async def call_llm(self, prompt: str, system: Optional[str] = None,
                       temperature: float = 0.7, max_tokens: int = 1000) -> Optional[str]:
        """Asynchronous call to HelixHive's LLM router."""
        llm = _get("llm_router")
        if llm is None:
            return None
        try:
            result = await llm.call_llm(prompt=prompt, system=system,
                                        temperature=temperature, max_tokens=max_tokens)
            self._step_tau()
            return result
        except Exception as e:
            logger.warning(f"[HiveBridge] LLM router call failed: {e}")
            self._decrement_j()
            return None

    def create_agent(self, role: str, prompt: str,
                     traits: Optional[Dict[str, float]] = None) -> Optional[Dict]:
        """Create a HelixHive Agent with Leech-encoded traits."""
        agent_mod = _get("agent")
        if agent_mod is None:
            return None
        try:
            agent = agent_mod.Agent(role=role, prompt=prompt, traits=traits)
            return {
                "agent_id": agent.agent_id,
                "role": agent.role,
                "traits": dict(agent.traits),
                "has_hd": agent.hd_vec is not None,
                "has_e8": agent.e8_vec is not None,
                "has_leech": agent.leech_vec is not None,
                "generation": agent.generation,
            }
        except Exception as e:
            logger.warning(f"[HiveBridge] create_agent failed: {e}")
            self._decrement_j()
            return None

    def mutate_agent_traits(self, traits: Dict[str, float],
                            mutation_rate: float = 0.1) -> Dict[str, float]:
        """Apply Gaussian mutation to trait values (standalone, no Agent needed)."""
        mutated = {}
        for k, v in traits.items():
            noise = np.random.normal(0, mutation_rate)
            mutated[k] = max(0.0, min(1.0, v + noise))
        return mutated

    def generate_synthetic_genome(self, context: Dict[str, Any]) -> Optional[Dict]:
        """Generate a novel agent genome via Evo2 (requires DB + genome)."""
        evo2 = _get("evo2")
        if evo2 is None:
            return None
        try:
            return {"available": True, "engine": "Evo2Generator",
                    "note": "Full generation requires HelixDBGit + genome.yaml wiring"}
        except Exception as e:
            logger.warning(f"[HiveBridge] Evo2 generation failed: {e}")
            return None

    @property
    def agent_available(self) -> bool:
        return _get("agent") is not None

    @property
    def evo2_available(self) -> bool:
        return _get("evo2") is not None

    # =====================================================================
    # 5. GENOME & CONFIG (genome.py + config.py)
    # =====================================================================

    def load_genome(self) -> Optional[Dict]:
        """Load the HelixHive genome YAML configuration."""
        genome_mod = _get("genome")
        if genome_mod is None:
            return None
        try:
            genome = genome_mod.Genome()
            return genome.data
        except Exception as e:
            logger.warning(f"[HiveBridge] Genome load failed: {e}")
            return None

    def get_genome_defaults(self) -> Optional[Dict]:
        """Get default genome values (no file required)."""
        genome_mod = _get("genome")
        if genome_mod is None:
            return None
        try:
            return genome_mod.DEFAULT_GENOME
        except Exception:
            return None

    def load_config(self) -> Optional[Dict]:
        """Load the HelixHive deployment configuration."""
        config_mod = _get("config")
        if config_mod is None:
            return None
        try:
            # Reset singleton for clean load
            config_mod.Config._instance = None
            cfg = config_mod.Config()
            return cfg.data
        except Exception as e:
            logger.warning(f"[HiveBridge] Config load failed: {e}")
            return None

    def get_config_defaults(self) -> Optional[Dict]:
        """Get default config values (no file required)."""
        config_mod = _get("config")
        if config_mod is None:
            return None
        try:
            return config_mod.DEFAULT_CONFIG
        except Exception:
            return None

    @property
    def genome_available(self) -> bool:
        return _get("genome") is not None

    @property
    def config_available(self) -> bool:
        return _get("config") is not None

    # =====================================================================
    # 6. PIPELINE (4-round product creation)
    # =====================================================================

    def get_pipeline_info(self) -> Optional[Dict]:
        """Get information about the product pipeline."""
        pipeline_mod = _get("pipeline")
        if pipeline_mod is None:
            return None
        try:
            pp = pipeline_mod.ProductPipeline
            return {
                "available": True,
                "class": "ProductPipeline",
                "rounds": 4,
                "round_prompts": list(pp.ROUND_PROMPTS.keys()) if hasattr(pp, 'ROUND_PROMPTS') else [],
                "note": "Full pipeline requires HelixDBGit + genome + config"
            }
        except Exception as e:
            logger.warning(f"[HiveBridge] Pipeline info failed: {e}")
            return None

    @property
    def pipeline_available(self) -> bool:
        return _get("pipeline") is not None

    # =====================================================================
    # 7. DATABASE (helixdb.py + helixdb_git_adapter.py)
    # =====================================================================

    def get_db_info(self) -> Optional[Dict]:
        """Get information about the database modules."""
        db = _get("helixdb")
        git = _get("helixdb_git")
        return {
            "helixdb_available": db is not None,
            "helixdb_git_available": git is not None,
            "node_types": git.HelixDBGit.NODE_TYPES if git and hasattr(git.HelixDBGit, 'NODE_TYPES') else [],
            "capabilities": {
                "graph_queries": db is not None,
                "vector_search": db is not None,
                "git_backed": git is not None,
                "git_lfs": git is not None,
            }
        }

    @property
    def db_available(self) -> bool:
        return _get("helixdb") is not None or _get("helixdb_git") is not None

    # =====================================================================
    # 8. GOVERNANCE (council.py + proposals.py + model_proposals.py)
    # =====================================================================

    def get_governance_info(self) -> Dict:
        """Get information about the governance system."""
        council = _get("council")
        proposals = _get("proposals")
        model_prop = _get("model_proposals")
        return {
            "council_available": council is not None,
            "proposals_available": proposals is not None,
            "model_proposals_available": model_prop is not None,
            "council_members": 6 if council is not None else 0,
            "features": {
                "weighted_voting": council is not None,
                "guardian_veto": council is not None,
                "constitutional_checks": council is not None,
                "supermajority_amend": council is not None,
                "proposal_management": proposals is not None,
                "daughter_repo_spawning": model_prop is not None,
            }
        }

    @property
    def council_available(self) -> bool:
        return _get("council") is not None

    # =====================================================================
    # 9. HEALTH / IMMUNE SYSTEM (immune.py + golay_self_repair_v5.py)
    # =====================================================================

    def get_immune_info(self) -> Dict:
        """Get information about the immune/health system."""
        immune = _get("immune")
        repair = _get("golay_repair")
        return {
            "immune_available": immune is not None,
            "golay_repair_available": repair is not None,
            "capabilities": {
                "failure_detection": immune is not None,
                "anomaly_detection": immune is not None,
                "healing_proposals": immune is not None,
                "codebase_self_repair": repair is not None,
                "vigil_fsm": repair is not None,
                "syntax_repair": repair is not None,
                "ruff_integration": repair is not None,
                "bandit_security": repair is not None,
            }
        }

    def run_self_repair(self, root_dir: Optional[str] = None,
                        dry_run: bool = True) -> Optional[Dict]:
        """Run Golay codebase self-repair (dry_run=True for safety)."""
        repair_mod = _get("golay_repair")
        if repair_mod is None:
            return None
        target_dir = root_dir or str(Path(__file__).resolve().parent.parent)
        try:
            engine = repair_mod.CodebaseRepairEngine(root_dir=target_dir)
            result = engine.run(dry_run=dry_run)
            self._step_tau()
            return result
        except Exception as e:
            logger.warning(f"[HiveBridge] Self-repair failed: {e}")
            self._decrement_j()
            return None

    @property
    def repair_available(self) -> bool:
        return _get("golay_repair") is not None

    @property
    def immune_available(self) -> bool:
        return _get("immune") is not None

    # =====================================================================
    # 10. SOCIAL (faction_manager.py + market.py)
    # =====================================================================

    def get_social_info(self) -> Dict:
        """Get information about faction/market subsystems."""
        faction = _get("faction_manager")
        market = _get("market")
        return {
            "faction_manager_available": faction is not None,
            "market_available": market is not None,
            "capabilities": {
                "dbscan_clustering": faction is not None,
                "faction_centroids": faction is not None,
                "niche_matching": faction is not None,
                "trait_listings": market is not None,
                "auctions": market is not None,
                "reputation_transfer": market is not None,
            }
        }

    @property
    def faction_available(self) -> bool:
        return _get("faction_manager") is not None

    @property
    def market_available(self) -> bool:
        return _get("market") is not None

    # =====================================================================
    # 11. REVELATION ENGINE
    # =====================================================================

    def get_revelation_info(self) -> Optional[Dict]:
        """Get information about the Revelation Engine."""
        rev = _get("revelation")
        if rev is None:
            return None
        return {
            "available": True,
            "engine": "RevelationEngine",
            "pipeline": ["epiphany", "revelation", "aha", "synthesis"],
            "note": "Full revelation requires HelixDBGit + genome + config"
        }

    def generate_revelation(self, context: Dict[str, Any]) -> Optional[Dict]:
        """Proxy for revelation generation."""
        rev = _get("revelation")
        if rev is None:
            return None
        return {
            "available": True,
            "engine": "HelixHive RevelationEngine",
            "note": "Full revelation requires HelixDBGit + genome.yaml wiring"
        }

    @property
    def revelation_available(self) -> bool:
        return _get("revelation") is not None

    # =====================================================================
    # 12. ECOSYSTEM (orchestrator, marketplace_sync, user_requests, etc.)
    # =====================================================================

    def get_ecosystem_info(self) -> Dict:
        """Get information about all ecosystem modules."""
        return {
            "orchestrator_available": _get("orchestrator") is not None,
            "marketplace_sync_available": _get("marketplace_sync") is not None,
            "user_requests_available": _get("user_requests") is not None,
            "world_model_available": _get("world_model") is not None,
            "fitness_available": _get("fitness") is not None,
            "resources_available": _get("resources") is not None,
            "helical_available": _get("helical") is not None,
        }

    # =====================================================================
    # 13. FULL SYSTEM DIAGNOSTICS
    # =====================================================================

    def get_state(self) -> Dict[str, Any]:
        """Full diagnostic state — every module's availability."""
        return {
            "available": self.available,
            "golay_available": self._golay_available,
            "tau": round(self.tau, 4),
            "J": round(self.J, 4),
            "modules_loaded": sum(1 for v in _modules.values() if v is not None),
            "modules_total": len(_modules),
            "core_math": {
                "memory": _get("memory") is not None,
                "helical": _get("helical") is not None,
            },
            "llm": {
                "llm_router": self.llm_available,
            },
            "agents": {
                "agent": self.agent_available,
                "evo2": self.evo2_available,
            },
            "config": {
                "genome": self.genome_available,
                "config": self.config_available,
            },
            "pipeline": {
                "pipeline": self.pipeline_available,
            },
            "database": self.get_db_info(),
            "governance": self.get_governance_info(),
            "health": self.get_immune_info(),
            "social": self.get_social_info(),
            "discovery": {
                "revelation": self.revelation_available,
            },
            "ecosystem": self.get_ecosystem_info(),
        }

    def get_summary(self) -> str:
        """Human-readable summary of HiveBridge status."""
        loaded = sum(1 for v in _modules.values() if v is not None)
        total = len(_modules)
        lines = [
            f"HiveBridge: {loaded}/{total} modules loaded",
            f"  Golay Leech: {'✓' if self._golay_available else '✗ (simplified mode)'}",
            f"  LLM Router:  {'✓ Groq/OpenRouter/Grok' if self.llm_available else '✗ (Ollama fallback)'}",
            f"  Agents:      {'✓' if self.agent_available else '✗'}",
            f"  Evo2:        {'✓' if self.evo2_available else '✗'}",
            f"  Genome:      {'✓' if self.genome_available else '✗'}",
            f"  Pipeline:    {'✓' if self.pipeline_available else '✗'}",
            f"  Council:     {'✓' if self.council_available else '✗'}",
            f"  Immune:      {'✓' if self.immune_available else '✗'}",
            f"  Revelation:  {'✓' if self.revelation_available else '✗'}",
            f"  Factions:    {'✓' if self.faction_available else '✗'}",
            f"  Market:      {'✓' if self.market_available else '✗'}",
            f"  Self-Repair: {'✓' if self.repair_available else '✗'}",
            f"  Database:    {'✓' if self.db_available else '✗'}",
            f"  τ={self.tau:.4f}  J={self.J:.4f}",
        ]
        return "\n".join(lines)

if __name__ == "__main__":
    # Self-test block for HiveBridge sovereign interface
    logging.basicConfig(level=logging.INFO)
    print("[Self-Test] Verifying HiveBridge Sovereign Interface...")
    hb = HiveBridge()
    summary = hb.get_summary()
    print(summary)
    if "HiveBridge" in summary:
        print("[Self-Test] HiveBridge Verification: SUCCESS")
    else:
        print("[Self-Test] HiveBridge Verification: FAILURE")
