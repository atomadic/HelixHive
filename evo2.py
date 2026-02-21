"""
Evo2 Generative Engine for HelixHive – creates synthetic agent genomes
using LLM prompts inspired by Evo2's generative capabilities.

Phase 1 implementation with full functionality: generates novel agent roles,
prompts, and trait combinations based on community context.
"""

import json
import logging
from typing import Dict, Any, Optional, List

from llm import call_llm
from memory import HD, LeechProjection
import helixdb

logger = logging.getLogger(__name__)


class Evo2Generator:
    """
    Evo2-style generative engine for agent genomes.
    Uses LLM with context-aware prompts to generate novel agents.
    """

    def __init__(self, db: 'helixdb.HelixDB', genome: Any, config: Any):
        """
        Initialize the generator.

        Args:
            db: HelixDB instance (for retrieving context)
            genome: Genome object (contains evo2 parameters)
            config: Config object (model selection, simulation mode)
        """
        self.db = db
        self.genome = genome
        self.config = config
        self.enabled = genome.data.get('evo2', {}).get('enabled', True)
        self.temperature = genome.data.get('evo2', {}).get('temperature', 0.8)
        self.max_tokens = genome.data.get('evo2', {}).get('max_tokens', 1000)

    def generate_agent_genome(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a novel agent genome (role, prompt, traits) conditioned on context.

        Args:
            context: Dictionary containing:
                - phase: current helical phase (0 or 1)
                - recent_successful_agents: list of agent summaries (optional)
                - faction_centroids: list of faction vectors (optional)
                - blackboard_highlights: recent influential messages (optional)
                - constraints: optional constraints (e.g., min/max traits)

        Returns:
            Dictionary with keys:
                - role: str
                - prompt: str
                - traits: dict (trait_name -> float in [0,1])
                - fitness_prediction: float (0-1) optional (if fitness predictor available)
        """
        if not self.enabled or self.config.data.get('simulation', False):
            logger.debug("Evo2 generator disabled or simulation mode; returning default")
            return self._default_genome()

        # Build prompt from context
        prompt = self._build_generation_prompt(context)

        system = "You are Evo2, a generative engine for agent genomes. Output only valid JSON."

        try:
            response = call_llm(
                prompt,
                system=system,
                model=self.config.data.get('model'),
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            genome = self._parse_genome_response(response)
            # Add fitness prediction if possible (optional)
            genome['fitness_prediction'] = self._estimate_fitness(genome)
            logger.info(f"Generated synthetic agent: {genome.get('role')}")
            return genome
        except Exception as e:
            logger.error(f"Evo2 generation failed: {e}")
            return self._default_genome()

    def generate_trait_combination(self, base_traits: Dict[str, float],
                                   constraints: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """
        Generate a novel trait combination for an existing agent.

        Args:
            base_traits: current traits of the agent
            constraints: optional constraints (e.g., keep certain traits fixed)

        Returns:
            New traits dictionary
        """
        if not self.enabled or self.config.data.get('simulation', False):
            return self._default_trait_mutation(base_traits)

        # Build prompt for trait combination
        fixed = constraints.get('fixed', []) if constraints else []
        prompt = self._build_trait_prompt(base_traits, fixed)

        system = "You are Evo2, a trait engineer. Output only JSON with trait names and float values."

        try:
            response = call_llm(
                prompt,
                system=system,
                model=self.config.data.get('model'),
                max_tokens=500,
                temperature=self.temperature
            )
            new_traits = self._parse_trait_response(response)
            # Ensure all original keys are present, clamp values
            for key in base_traits:
                if key not in new_traits:
                    new_traits[key] = base_traits[key]
            for key, val in new_traits.items():
                new_traits[key] = max(0.0, min(1.0, val))
            return new_traits
        except Exception as e:
            logger.error(f"Trait generation failed: {e}")
            return self._default_trait_mutation(base_traits)

    def mutate_genome(self, genome: Dict[str, Any], mutation_rate: float = 0.1) -> Dict[str, Any]:
        """
        Apply context-aware mutation to a genome.

        Args:
            genome: dict with 'role', 'prompt', 'traits'
            mutation_rate: base mutation rate

        Returns:
            Mutated genome
        """
        if not self.enabled or self.config.data.get('simulation', False):
            return self._default_genome_mutation(genome, mutation_rate)

        # Build mutation prompt
        prompt = self._build_mutation_prompt(genome, mutation_rate)

        system = "You are Evo2, a genome mutator. Output only JSON with the mutated genome."

        try:
            response = call_llm(
                prompt,
                system=system,
                model=self.config.data.get('model'),
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            mutated = self._parse_genome_response(response)
            # Ensure required fields
            if 'role' not in mutated:
                mutated['role'] = genome['role'] + "_mutated"
            if 'prompt' not in mutated:
                mutated['prompt'] = genome['prompt']
            if 'traits' not in mutated:
                mutated['traits'] = genome['traits']
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

    def _build_trait_prompt(self, base_traits: Dict[str, float], fixed: List[str]) -> str:
        """Construct prompt for generating a new trait combination."""
        fixed_str = ", ".join(fixed) if fixed else "none"
        traits_str = "\n".join([f"  {k}: {v}" for k, v in base_traits.items()])
        return f"""Given the following current traits of an agent:
{traits_str}

Generate a new, improved trait combination by making small, intelligent adjustments.
Do not change these fixed traits: {fixed_str}
The new traits should still sum to roughly the same total? No, just each between 0 and 1.

Output ONLY a JSON object with trait names as keys and float values.
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
            # Find JSON block
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                data = json.loads(json_str)
                # Validate required keys
                if not all(k in data for k in ('role', 'prompt', 'traits')):
                    raise ValueError("Missing required keys")
                # Ensure traits are floats in [0,1]
                for k, v in data['traits'].items():
                    data['traits'][k] = max(0.0, min(1.0, float(v)))
                return data
            else:
                raise ValueError("No JSON found")
        except Exception as e:
            logger.error(f"Failed to parse genome response: {e}")
            raise

    def _parse_trait_response(self, response: str) -> Dict[str, float]:
        """Parse LLM response into a traits dictionary."""
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                data = json.loads(json_str)
                # Convert all values to float
                return {k: float(v) for k, v in data.items()}
            else:
                raise ValueError("No JSON found")
        except Exception as e:
            logger.error(f"Failed to parse trait response: {e}")
            raise

    def _estimate_fitness(self, genome: Dict[str, Any]) -> float:
        """Optional fitness estimation (placeholder)."""
        # Could call fitness predictor if available, but for now return moderate
        return 0.6

    def _default_genome(self) -> Dict[str, Any]:
        """Return a default genome when generation fails."""
        return {
            'role': 'default_synthetic',
            'prompt': 'You are a helpful AI agent, focused on creative problem-solving.',
            'traits': {'creativity': 0.7, 'thoroughness': 0.5, 'cooperativeness': 0.6},
            'fitness_prediction': 0.5
        }

    def _default_trait_mutation(self, traits: Dict[str, float]) -> Dict[str, float]:
        """Simple random mutation fallback."""
        import random
        new_traits = {}
        for k, v in traits.items():
            new_traits[k] = max(0.0, min(1.0, v + random.gauss(0, 0.1)))
        return new_traits

    def _default_genome_mutation(self, genome: Dict[str, Any], rate: float) -> Dict[str, Any]:
        """Simple mutation fallback."""
        import random
        mutated = genome.copy()
        # Mutate traits
        new_traits = {}
        for k, v in genome.get('traits', {}).items():
            new_traits[k] = max(0.0, min(1.0, v + random.gauss(0, rate)))
        mutated['traits'] = new_traits
        # Optionally mutate role
        if random.random() < rate:
            mutated['role'] = genome.get('role', 'agent') + "_mut"
        return mutated


# Convenience function for external use
def generate_synthetic_agent(db: 'helixdb.HelixDB', genome: Any, config: Any,
                             context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a synthetic agent genome using Evo2.
    """
    generator = Evo2Generator(db, genome, config)
    return generator.generate_agent_genome(context)
