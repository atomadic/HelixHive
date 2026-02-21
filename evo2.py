"""
Evo2 Generative Engine for HelixHive Phase 2.
Creates synthetic agent genomes (role, prompt, traits) using LLM prompts
conditioned on community context (faction centroids, recent successes, phase).
All generated genomes are Leech‑grounded and Golay‑certified.
"""

import json
import logging
import time
from typing import Dict, Any, Optional, List, Tuple
import numpy as np

from llm_router import call_llm
from memory import HD, leech_encode, _LEECH_PROJ, LeechErrorCorrector
from helixdb_git_adapter import HelixDBGit
from genome import Genome
from config import Config

logger = logging.getLogger(__name__)


class Evo2Generator:
    """
    Evo2‑style generative engine for agent genomes.
    Uses LLM with context‑aware prompts to generate novel agents.
    All generated agents have Leech vectors and Golay certificates.
    """

    def __init__(self, db: HelixDBGit, genome: Genome, config: Config):
        """
        Args:
            db: Database adapter (for retrieving context)
            genome: Genome object (contains evo2 parameters)
            config: Config object (model selection, simulation mode)
        """
        self.db = db
        self.genome = genome
        self.config = config
        self.enabled = genome.get('evo2.enabled', True)
        self.temperature = genome.get('evo2.temperature', 0.8)
        self.max_tokens = genome.get('evo2.max_tokens', 1000)

    # ----------------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------------

    async def generate_agent_genome(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a novel agent genome (role, prompt, traits) conditioned on context.

        Args:
            context: Dictionary containing:
                - phase: current helical phase (0 or 1)
                - faction_centroids: list of faction Leech vectors (optional)
                - recent_successful_agents: list of agent summaries (optional)
                - blackboard_highlights: recent influential messages (optional)

        Returns:
            Dictionary with keys:
                - role: str
                - prompt: str
                - traits: dict (trait_name -> float in [0,1])
                - leech_vector: list (24 ints) – Golay‑certified Leech point
                - syndrome: int (0 if perfect)
        """
        if not self.enabled or self.config.get('simulation', False):
            logger.debug("Evo2 generator disabled or simulation mode; returning default")
            return self._default_genome()

        # Build prompt from context
        prompt = self._build_generation_prompt(context)

        system = "You are Evo2, a generative engine for agent genomes. Output only valid JSON."

        try:
            response = await call_llm(
                prompt,
                system=system,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            genome_dict = self._parse_genome_response(response)
            # Compute Leech vector for the agent (from role and traits)
            leech_vec = self._compute_agent_leech(genome_dict)
            # Golay repair
            corrected, syndrome = LeechErrorCorrector.correct(leech_vec)
            genome_dict['leech_vector'] = corrected.tolist()
            genome_dict['syndrome'] = int(syndrome)
            logger.info(f"Generated synthetic agent: {genome_dict.get('role')}")
            return genome_dict
        except Exception as e:
            logger.error(f"Evo2 generation failed: {e}")
            return self._default_genome()

    async def mutate_genome(self, genome: Dict[str, Any], mutation_rate: float = 0.1) -> Dict[str, Any]:
        """
        Apply context‑aware mutation to a genome.
        Uses LLM to propose intelligent mutations, then Golay‑repairs the resulting Leech vector.
        """
        if not self.enabled or self.config.get('simulation', False):
            return self._default_genome_mutation(genome, mutation_rate)

        # Build mutation prompt
        prompt = self._build_mutation_prompt(genome, mutation_rate)
        system = "You are Evo2, a genome mutator. Output only JSON with the mutated genome."

        try:
            response = await call_llm(
                prompt,
                system=system,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            mutated = self._parse_genome_response(response)
            # Ensure required fields
            if 'role' not in mutated:
                mutated['role'] = genome['role'] + "_mutated"
            if 'prompt' not in mutated:
                mutated['prompt'] = genome['prompt']
            if 'traits' not in mutated:
                mutated['traits'] = genome['traits']

            # Compute new Leech vector and repair
            leech_vec = self._compute_agent_leech(mutated)
            corrected, syndrome = LeechErrorCorrector.correct(leech_vec)
            mutated['leech_vector'] = corrected.tolist()
            mutated['syndrome'] = int(syndrome)
            return mutated
        except Exception as e:
            logger.error(f"Mutation failed: {e}")
            return self._default_genome_mutation(genome, mutation_rate)

    # ----------------------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------------------

    def _build_generation_prompt(self, context: Dict[str, Any]) -> str:
        """Construct prompt for generating a new agent genome."""
        phase = context.get('phase', 0)
        recent = context.get('recent_successful_agents', [])
        factions = context.get('faction_centroids', [])
        blackboard = context.get('blackboard_highlights', '')

        recent_str = "\n".join([f"- {a}" for a in recent[:3]]) if recent else "None"
        faction_str = f"{len(factions)} active factions" if factions else "No factions"

        return f"""Generate a novel agent genome for HelixHive.

Current helical phase: {phase} (0=expansion, 1=refinement)
Recent successful agents: {recent_str}
{faction_str}
Recent community discussions: {blackboard[:200] if blackboard else 'None'}

Create an agent with:
- role: a short, descriptive name (e.g., "visionary", "engineer")
- prompt: a system prompt for this agent (around 200-300 words)
- traits: an object with numeric values between 0 and 1. Common traits: creativity, thoroughness, cooperativeness, ambition, curiosity. You may include other relevant traits.

Output ONLY a JSON object with keys: "role", "prompt", "traits".
"""

    def _build_mutation_prompt(self, genome: Dict[str, Any], rate: float) -> str:
        """Construct prompt for mutating a genome."""
        role = genome.get('role', 'unknown')
        prompt = genome.get('prompt', '')[:200]
        traits = genome.get('traits', {})
        traits_str = ", ".join([f"{k}={v}" for k, v in traits.items()])
        return f"""Mutate the following agent genome with mutation rate {rate}:

Role: {role}
Prompt excerpt: {prompt}...
Traits: {traits_str}

Generate a mutated version by:
- Possibly adjusting the role slightly (e.g., add a suffix)
- Modifying the prompt to be slightly different
- Adjusting trait values by small amounts (keeping within 0-1)

Output ONLY a JSON object with keys: "role", "prompt", "traits".
"""

    def _parse_genome_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into a genome dictionary."""
        try:
            # Find JSON block (handles markdown code fences)
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON object directly
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = response[start:end]
                else:
                    raise ValueError("No JSON found")
            data = json.loads(json_str)
            # Validate required keys
            if not all(k in data for k in ('role', 'prompt', 'traits')):
                raise ValueError("Missing required keys")
            # Ensure traits are floats in [0,1]
            for k, v in data['traits'].items():
                data['traits'][k] = max(0.0, min(1.0, float(v)))
            return data
        except Exception as e:
            logger.error(f"Failed to parse genome response: {e}")
            raise

    def _compute_agent_leech(self, genome: Dict[str, Any]) -> np.ndarray:
        """
        Compute a Leech vector for an agent from its role and traits.
        Method: Bundle role HD vector with weighted trait key HD vectors,
        project to 24D, encode to Leech lattice.
        """
        role_vec = HD.from_word(genome['role']).astype(np.float32)
        # Weighted sum of trait key vectors
        trait_sum = np.zeros(HD.DIM, dtype=np.float32)
        for key, val in genome['traits'].items():
            key_vec = HD.from_word(key).astype(np.float32)
            trait_sum += val * key_vec
        combined = role_vec + trait_sum
        # Project to 24D
        leech_float = np.dot(combined, _LEECH_PROJ)
        return leech_encode(leech_float)

    def _default_genome(self) -> Dict[str, Any]:
        """Return a default genome when generation fails."""
        default = {
            'role': 'default_synthetic',
            'prompt': 'You are a helpful AI agent, focused on creative problem-solving.',
            'traits': {'creativity': 0.7, 'thoroughness': 0.5, 'cooperativeness': 0.6},
        }
        leech_vec = self._compute_agent_leech(default)
        corrected, syndrome = LeechErrorCorrector.correct(leech_vec)
        default['leech_vector'] = corrected.tolist()
        default['syndrome'] = int(syndrome)
        return default

    def _default_genome_mutation(self, genome: Dict[str, Any], rate: float) -> Dict[str, Any]:
        """Simple mutation fallback (adds Gaussian noise to traits)."""
        import random
        mutated = genome.copy()
        new_traits = {}
        for k, v in genome.get('traits', {}).items():
            new_traits[k] = max(0.0, min(1.0, v + random.gauss(0, rate)))
        mutated['traits'] = new_traits
        # Optionally mutate role
        if random.random() < rate:
            mutated['role'] = genome.get('role', 'agent') + "_mut"
        # Recompute Leech vector
        leech_vec = self._compute_agent_leech(mutated)
        corrected, syndrome = LeechErrorCorrector.correct(leech_vec)
        mutated['leech_vector'] = corrected.tolist()
        mutated['syndrome'] = int(syndrome)
        return mutated


# ----------------------------------------------------------------------
# Convenience function for external use
# ----------------------------------------------------------------------

async def generate_synthetic_agent(db: HelixDBGit, genome: Genome, config: Config,
                                   context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a synthetic agent genome using Evo2.
    """
    generator = Evo2Generator(db, genome, config)
    return await generator.generate_agent_genome(context)
