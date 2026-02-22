"""
Phase 2 Enhanced Product Pipeline for HelixHive (GitHub‑native)

Generates Leech‑certified, agentic, self‑building products through 4 enhancement rounds:
1. Leech depth – initial concept
2. Personalization – audience adaptation
3. Agentic bundles – self‑building Notion/ClickUp, voice AI, executable templates
4. Monetization – outcome pricing, Leech‑NFT provenance, marketplace JSON export

Every round includes Golay self‑repair, faction‑aware creator selection, and LLM grounding.
Final products are committed to the marketplace folder and stored in the database.
"""

import logging
import json
import time
import os
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from agent import Agent
from llm_router import HelixLLMRouter
from fitness import FitnessPredictor
from memory import LeechDecoder, LeechErrorCorrector, HD, _LEECH_PROJ
from revelation import RevelationEngine
from helixdb_git_adapter import HelixDBGit
from faction_manager import FactionManager  # new Phase 2 module (assumed)
from golay_self_repair import GolaySelfRepairEngine

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
MARKETPLACE_AGENTS_DIR = Path("marketplace") / "agents"


class ProductPipeline:
    """
    Orchestrates the 4‑round product creation pipeline with Golay hardening.
    """

    # Round prompts with 2026 trends embedded
    ROUND_PROMPTS = {
        1: (
            "Create an initial product concept for the niche: {niche}. "
            "Return a JSON object with exactly these fields:\n"
            "  - title: string (product name)\n"
            "  - description: string (1‑2 paragraphs)\n"
            "  - features: list of strings\n"
            "  - is_template: boolean (true if this can become an executable agent template)\n"
            "No other text, only JSON."
        ),
        2: (
            "Refine the product for the target audience: {audience}. "
            "Add personalization elements that would increase conversion by 40% (2026 trend). "
            "Return the updated JSON with the same structure."
        ),
        3: (
            "Add agentic executable components: describe how this product can be delivered as "
            "a self‑building Notion/ClickUp dashboard, an AI voice pack, or an executable agent template. "
            "Include a 'agentic_components' field (list of strings) in the JSON. "
            "Return the updated JSON."
        ),
        4: (
            "Add monetization and provenance: suggest a price tier (e.g., $29 one‑time or $9/mo sponsorship), "
            "include a Leech certificate placeholder, and describe an outcome guarantee. "
            "Add fields: 'price' (object with one_time and/or sponsors_tier), "
            "'outcome_guarantee' (string), 'leech_certificate' (object with syndrome=0 and hash). "
            "Return the final JSON."
        ),
    }

    def __init__(self, db: HelixDBGit, genome: Any, config: Any, simulate: bool = False):
        """
        Args:
            db: Git‑backed database adapter.
            genome: Genome object (with helicity, pipeline settings).
            config: Config object (model choices, etc.).
            simulate: If True, bypass LLM and use dummy responses.
        """
        self.db = db
        self.genome = genome
        self.config = config
        self.simulate = simulate
        self.router = HelixLLMRouter()
        self.fitness = FitnessPredictor(db, genome)
        self.faction_mgr = FactionManager(db)   # assumes faction manager exists
        self.repair_engine = GolaySelfRepairEngine(db, genome.data.get('tick', 0))

        # Ensure marketplace directory exists
        MARKETPLACE_AGENTS_DIR.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def run(self, niche: str, agents: List[Agent], user_context: Optional[Dict] = None) -> List[str]:
        """
        Run the full pipeline for a given niche.
        Returns list of product IDs created.
        """
        logger.info(f"🚀 Starting Phase 2 pipeline for niche: {niche}")

        # Ensure we have at least one agent
        if not agents:
            logger.warning("No agents available; spawning default via Revelation")
            agents = [self._spawn_default_agent()]

        # Select creator using faction intelligence
        creator = self.faction_mgr.select_best_creator(agents, niche)
        logger.info(f"Faction‑routed creator: {creator.role} (faction {getattr(creator, 'faction_id', 'unknown')})")

        # Round 1: initial creation
        product = self._create_product(creator, niche, round_num=1)
        if not product:
            logger.error("Round 1 failed; aborting pipeline")
            return []

        # Rounds 2‑4 with Golay repair after each
        for round_num in range(2, 5):
            logger.info(f"Round {round_num} – Golay repair active")
            product = self._refine_product(product, creator, round_num, user_context)
            if not product:
                logger.error(f"Round {round_num} failed; aborting pipeline")
                return []

            # Golay self‑repair on product's Leech vector (if present)
            if "leech_vector" in product:
                corrected, syndrome = LeechErrorCorrector.correct(np.array(product["leech_vector"]))
                if syndrome != 0:
                    logger.info(f"Round {round_num} product repaired (syndrome={syndrome})")
                    product["leech_vector"] = corrected.tolist()
                    product.setdefault("repair_history", []).append({
                        "round": round_num,
                        "syndrome": int(syndrome),
                        "timestamp": time.time()
                    })

        # Final scoring
        score = self._score_product(product, creator)
        logger.info(f"Final product score: {score:.3f}")

        # Store product in database
        product_id = self._store_product(product, creator, score)
        logger.info(f"Product stored: {product_id}")

        # If template, create marketplace entry and commit JSON
        if product.get("is_template"):
            template_id = self._store_template(product, creator, product_id)
            logger.info(f"Template created: {template_id}")
            self._export_to_marketplace(product, product_id, template_id)

        return [product_id]

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _spawn_default_agent(self) -> Agent:
        """Create a default agent using Revelation Engine."""
        try:
            rev = RevelationEngine(self.db, self.genome, self.config)
            context = {
                'phase': self.genome.data.get('helicity', {}).get('current_phase', 0),
                'recent_proposals': '',
                'factions': '',
                'health': 'bootstrap',
                'agent_count': 0
            }
            proposal_data = rev.generate(context)
            if proposal_data and proposal_data.get('rating', 0) > 0.6:
                role = proposal_data.get('role', 'default_creator')
                prompt = proposal_data.get('details', 'You are a creative product generator.')
                traits = proposal_data.get('traits', {})
                for k in traits:
                    traits[k] = max(0.0, min(1.0, traits[k]))
                agent = Agent(
                    role=role,
                    prompt=prompt,
                    traits=traits,
                    generation=0,
                    synthetic=True
                )
                agent.save_to_db(self.db)
                return agent
        except Exception as e:
            logger.warning(f"Revelation Engine failed: {e}")

        # Fallback default
        agent = Agent(
            role="default_creator",
            prompt="You are a creative product generator.",
            traits={"creativity": 0.7, "thoroughness": 0.7, "cooperativeness": 0.5},
            generation=0
        )
        agent.save_to_db(self.db)
        return agent

    def _call_llm_structured(self, prompt: str, system: str, leech_vec: Optional[np.ndarray] = None,
                             expected_keys: List[str] = None) -> Optional[Dict]:
        """
        Call LLM with grounding, enforce JSON output, retry once on failure.
        """
        if self.simulate:
            # Return a plausible dummy response
            return {
                "title": "Simulated Product",
                "description": "This is a simulated product for testing.",
                "features": ["feature1", "feature2"],
                "is_template": True,
                "price": {"one_time": 29},
                "outcome_guarantee": "30‑day satisfaction",
                "leech_certificate": {"syndrome": 0, "hash": "sim"}
            }

        for attempt in range(2):
            try:
                response = self.router.call(prompt, system=system, leech_vector=leech_vec)
                # Attempt to parse JSON
                data = json.loads(response)
                # Optionally validate expected keys
                if expected_keys and not all(k in data for k in expected_keys):
                    logger.warning(f"LLM response missing keys {expected_keys}, attempt {attempt+1}")
                    continue
                return data
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"LLM call attempt {attempt+1} failed: {e}")
                if attempt == 0:
                    # Retry with a more explicit instruction
                    prompt += "\n\nIMPORTANT: Your response must be valid JSON only, no other text."
        return None

    def _create_product(self, agent: Agent, niche: str, round_num: int) -> Optional[Dict]:
        """Round 1: initial creation."""
        prompt = self.ROUND_PROMPTS[round_num].format(niche=niche)
        system = f"You are {agent.role}, a creative product generator."
        leech_vec = agent.leech_vec if agent.leech_vec is not None else None

        data = self._call_llm_structured(prompt, system, leech_vec,
                                         expected_keys=["title", "description", "features", "is_template"])
        if not data:
            return None

        # Add metadata
        data["niche"] = niche
        data["created_at"] = time.time()
        data["round"] = round_num
        data["creator_id"] = agent.agent_id
        data["leech_vector"] = self._compute_product_leech(data.get("description", ""))
        return data

    def _refine_product(self, product: Dict, agent: Agent, round_num: int,
                        user_context: Optional[Dict]) -> Optional[Dict]:
        """Refine product with round‑specific prompt."""
        audience = user_context.get("target_audience", "general") if user_context else "general"
        prompt = self.ROUND_PROMPTS[round_num].format(audience=audience)
        # Include current product JSON in prompt
        current_json = json.dumps(product, indent=2)
        full_prompt = f"Current product:\n{current_json}\n\n{prompt}\n\nReturn updated JSON."
        system = f"You are {agent.role}, a product refiner."
        leech_vec = agent.leech_vec if agent.leech_vec is not None else None

        # For rounds 3 and 4, expected keys may expand; we don't strictly enforce all.
        data = self._call_llm_structured(full_prompt, system, leech_vec)
        if not data:
            return product   # keep previous version

        # Merge with original
        product.update(data)
        product["round"] = round_num
        product["updated_at"] = time.time()
        # Recompute Leech vector if description changed
        if "description" in data:
            product["leech_vector"] = self._compute_product_leech(product.get("description", ""))
        return product

    def _compute_product_leech(self, text: str) -> List[int]:
        """Generate a Leech vector from product description (bag‑of‑words)."""
        words = text.split()[:200]
        if not words:
            return [0] * 24
        word_vecs = [HD.from_word(w) for w in words]
        hd_vec = HD.bundle(word_vecs)
        leech_float = np.dot(hd_vec.astype(np.float32), _LEECH_PROJ)
        leech_vec = LeechDecoder.leech_closest_point(leech_float)
        return leech_vec.tolist()

    def _score_product(self, product: Dict, agent: Agent) -> float:
        """Score product using fitness predictor."""
        context = {
            "phase": self.genome.data.get('helicity', {}).get('current_phase', 0),
            "description": product.get("description", ""),
            "agent_id": agent.agent_id,
            "niche": product.get("niche", "")
        }
        # If product has its own Leech vector, use it; otherwise compute
        vec = product.get("leech_vector")
        if vec is None:
            vec = self._compute_product_leech(product.get("description", ""))
        fitness, _ = self.fitness.predict(
            'product',
            f"temp_{time.time()}",
            target_vector=np.array(vec),
            context=context
        )
        return fitness

    def _store_product(self, product: Dict, agent: Agent, score: float) -> str:
        """Store product in database and return its ID."""
        product_id = f"prod_{int(time.time())}_{agent.agent_id[:8]}"
        node_data = {
            "id": product_id,
            "type": "Product",
            "title": product.get("title"),
            "description": product.get("description"),
            "features": product.get("features", []),
            "niche": product.get("niche"),
            "creator_id": agent.agent_id,
            "score": score,
            "is_template": product.get("is_template", False),
            "round": product.get("round"),
            "created_at": product.get("created_at", time.time()),
            "repair_history": product.get("repair_history", [])
        }
        self.db.update_properties(product_id, node_data)

        # Store Leech vector
        if "leech_vector" in product:
            self.db.update_vector(product_id, "Product", "leech", np.array(product["leech_vector"]))

        return product_id

    def _store_template(self, product: Dict, agent: Agent, product_id: str) -> str:
        """Create a template node for marketplace."""
        template_id = f"tmpl_{int(time.time())}_{agent.agent_id[:8]}"
        repo_name = f"helixhive-{product.get('niche', 'template').replace(' ', '-').lower()}-{template_id[-6:]}"

        # Build Leech certificate (placeholder, actual cert generated by Golay on spawn)
        leech_cert = {
            "syndrome": 0,
            "hash": f"leech-{hash(template_id)}",  # placeholder
            "vector": product.get("leech_vector", [])
        }

        node_data = {
            "id": template_id,
            "type": "Template",
            "title": product.get("title"),
            "description": product.get("description"),
            "faction": getattr(agent, "faction", agent.role),  # fallback
            "price": product.get("price", {"one_time": 29}),
            "template_repo": repo_name,
            "leech_certificate": leech_cert,
            "created_at": time.time(),
            "creator_id": agent.agent_id,
            "product_id": product_id,
        }
        self.db.update_properties(template_id, node_data)

        # Copy product's Leech vector
        if "leech_vector" in product:
            self.db.update_vector(template_id, "Template", "leech", np.array(product["leech_vector"]))

        return template_id

    def _export_to_marketplace(self, product: Dict, product_id: str, template_id: str):
        """
        Write a JSON file to marketplace/agents/ and stage it for commit.
        (Actual commit handled by orchestrator.)
        """
        # Build marketplace listing
        listing = {
            "id": template_id,
            "product_id": product_id,
            "title": product.get("title"),
            "description": product.get("description"),
            "faction": product.get("faction", "General"),
            "price": product.get("price", {"one_time": 29}),
            "template_repo": product.get("template_repo", f"helixhive-{product_id}"),
            "leech_certificate": product.get("leech_certificate", {"syndrome": 0, "hash": ""}),
            "created_at": product.get("created_at", time.time()),
            "spawn_url": f"https://github.com/new?template_name={product.get('template_repo', '')}&owner=atomadic"
        }

        file_path = MARKETPLACE_AGENTS_DIR / f"{template_id}.json"
        with open(file_path, "w") as f:
            json.dump(listing, f, indent=2)

        logger.info(f"Marketplace JSON exported: {file_path}")


# -----------------------------------------------------------------------------
# Convenience function for orchestrator
# -----------------------------------------------------------------------------
def run_pipeline(niche: str, agents: List[Agent], genome: Any, config: Any,
                 db: HelixDBGit, simulate: bool = False) -> List[str]:
    """
    Run the product pipeline.
    Returns list of product IDs created.
    """
    pipeline = ProductPipeline(db, genome, config, simulate)
    return pipeline.run(niche, agents)
