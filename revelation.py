"""
Revelation Engine for HelixHive – generates epiphanies, revelations, and AHA moments
to synthesize novel proposals. Grounded in E8/Leech geometry and helical phase.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

from llm import call_llm
from memory import HD, E8, LeechProjection
import helixdb

logger = logging.getLogger(__name__)


class RevelationEngine:
    """
    Generates structured insights using LLM and geometric grounding.
    """

    def __init__(self, db: 'helixdb.HelixDB', genome: Any, config: Any):
        self.db = db
        self.genome = genome
        self.config = config
        self.current_phase = genome.data.get('helicity', {}).get('current_phase', 0)

        # Drift protection thresholds
        self.drift_threshold = 2.0  # E8 distance units

    # ----------------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------------

    def generate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a full revelation cycle: 5 epiphanies, each with 5 revelations,
        each with 3 AHA moments. Synthesize the strongest insights into a final proposal.
        Returns a dict with the final proposal and its rating.
        """
        logger.info("Starting Revelation Engine cycle")

        # Step 1: Generate 5 epiphanies
        epiphanies = self._generate_epiphanies(context, n=5)

        all_revelations = []
        all_ahas = []

        # Step 2: For each epiphany, generate 5 revelations
        for epi in epiphanies:
            revelations = self._generate_revelations(epi, context, n=5)
            all_revelations.extend(revelations)

            # Step 3: For each revelation, generate 3 AHA moments
            for rev in revelations:
                ahas = self._generate_ahas(rev, context, n=3)
                all_ahas.extend(ahas)

        logger.info(f"Generated {len(epiphanies)} epiphanies, "
                    f"{len(all_revelations)} revelations, {len(all_ahas)} AHA moments")

        # Step 4: Synthesize the strongest insights
        final_proposal = self._synthesize(epiphanies, all_revelations, all_ahas, context)

        # Step 5: Rate the final proposal
        rating = self._rate_proposal(final_proposal, context)

        # If rating >= 0.92, optionally feed back (but we'll just return for now)
        final_proposal['rating'] = rating
        final_proposal['timestamp'] = datetime.now().timestamp()

        return final_proposal

    # ----------------------------------------------------------------------
    # Generation steps
    # ----------------------------------------------------------------------

    def _generate_epiphanies(self, context: Dict[str, Any], n: int = 5) -> List[str]:
        """
        Generate n epiphanies using LLM, guided by context and phase.
        """
        if self.config.data.get('simulation', False):
            # Deterministic simulation mode
            return [f"Simulated epiphany {i+1}" for i in range(n)]

        # Build prompt
        system = "You are a creative insight generator. Generate high-level epiphanies about the HelixHive community and its evolution."
        user = self._build_epiphany_prompt(context, n)
        try:
            response = call_llm(user, system=system, max_tokens=1000, temperature=0.9)
            # Parse response (expect list of strings)
            epiphanies = self._parse_list_response(response, n)
            # Drift check: compute geometric coherence of each epiphany
            epiphanies = [self._drift_check_epiphany(e) for e in epiphanies]
            return epiphanies[:n]
        except Exception as e:
            logger.error(f"Epiphany generation failed: {e}")
            return [f"Fallback epiphany {i+1}" for i in range(n)]

    def _generate_revelations(self, epiphany: str, context: Dict[str, Any], n: int = 5) -> List[str]:
        """
        Generate n revelations for a given epiphany.
        """
        if self.config.data.get('simulation', False):
            return [f"Simulated revelation {i+1} for: {epiphany[:30]}" for i in range(n)]

        system = "You are a deep thinker. Expand an epiphany into detailed revelations."
        user = self._build_revelation_prompt(epiphany, context, n)
        try:
            response = call_llm(user, system=system, max_tokens=1000, temperature=0.8)
            revelations = self._parse_list_response(response, n)
            # Drift check for each revelation
            revelations = [self._drift_check_revelation(r) for r in revelations]
            return revelations[:n]
        except Exception as e:
            logger.error(f"Revelation generation failed: {e}")
            return [f"Fallback revelation {i+1}" for i in range(n)]

    def _generate_ahas(self, revelation: str, context: Dict[str, Any], n: int = 3) -> List[str]:
        """
        Generate n paradigm-shattering AHA moments from a revelation.
        """
        if self.config.data.get('simulation', False):
            return [f"Simulated AHA {i+1} from: {revelation[:30]}" for i in range(n)]

        system = "You are a visionary. Extract concrete, paradigm-shattering AHA moments from a revelation."
        user = self._build_aha_prompt(revelation, context, n)
        try:
            response = call_llm(user, system=system, max_tokens=800, temperature=0.9)
            ahas = self._parse_list_response(response, n)
            # Drift check for each AHA
            ahas = [self._drift_check_aha(a) for a in ahas]
            return ahas[:n]
        except Exception as e:
            logger.error(f"AHA generation failed: {e}")
            return [f"Fallback AHA {i+1}" for i in range(n)]

    def _synthesize(self, epiphanies: List[str], revelations: List[str],
                    ahas: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesize the strongest insights into a final proposal.
        Uses LLM to combine and refine.
        """
        if self.config.data.get('simulation', False):
            return {
                'summary': 'Simulated synthetic proposal',
                'details': 'Generated from simulation',
                'novelty_score': 0.7,
                'coherence_score': 0.7,
                'impact_score': 0.7,
                'feasibility_score': 0.7,
                'geometric_coherence': 0.8
            }

        # Select top insights (simple heuristic: first few)
        top_epi = epiphanies[:3]
        top_rev = revelations[:5]
        top_aha = ahas[:5]

        system = "You are a synthesis engine. Combine the best insights into a coherent, novel proposal for HelixHive."
        user = self._build_synthesis_prompt(top_epi, top_rev, top_aha, context)
        try:
            response = call_llm(user, system=system, max_tokens=1500, temperature=0.7)
            # Expect JSON with fields
            proposal = self._parse_proposal_response(response)
            # Add geometric coherence (placeholder)
            proposal['geometric_coherence'] = 0.9  # TODO compute from E8 distance
            return proposal
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return {
                'summary': 'Fallback proposal',
                'details': 'Synthesis failed',
                'novelty_score': 0.5,
                'coherence_score': 0.5,
                'impact_score': 0.5,
                'feasibility_score': 0.5,
                'geometric_coherence': 0.5
            }

    def _rate_proposal(self, proposal: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Rate the final proposal on novelty, coherence, impact, feasibility.
        Returns weighted average.
        """
        # For Phase 1, we use the scores already in the proposal (from LLM)
        # But we could also compute our own using geometric methods.
        n = proposal.get('novelty_score', 0.5)
        c = proposal.get('coherence_score', 0.5)
        i = proposal.get('impact_score', 0.5)
        f = proposal.get('feasibility_score', 0.5)
        # Simple average
        rating = (n + c + i + f) / 4.0
        return rating

    # ----------------------------------------------------------------------
    # Drift protection
    # ----------------------------------------------------------------------

    def _drift_check_epiphany(self, text: str) -> str:
        """Check if epiphany is too far from known knowledge; if so, dampen."""
        # Placeholder: for now, return as-is.
        # In future, compute E8 embedding of text and compare to knowledge base.
        return text

    def _drift_check_revelation(self, text: str) -> str:
        return text

    def _drift_check_aha(self, text: str) -> str:
        return text

    # ----------------------------------------------------------------------
    # Prompt builders
    # ----------------------------------------------------------------------

    def _build_epiphany_prompt(self, context: Dict[str, Any], n: int) -> str:
        phase = self.current_phase
        # Include recent successful proposals, faction info, etc.
        return f"""
Generate {n} high-level epiphanies about the HelixHive community.

Current helical phase: {phase} (0=expansion, 1=refinement)
Recent successful proposals: {context.get('recent_proposals', 'None')}
Dominant factions: {context.get('factions', 'None')}
Community health: {context.get('health', 'stable')}

Epiphanies should be profound, insightful, and guide the evolution of the community.
List each epiphany on a new line, starting with "Epiphany:".
"""

    def _build_revelation_prompt(self, epiphany: str, context: Dict[str, Any], n: int) -> str:
        return f"""
Expand the following epiphany into {n} detailed revelations.

Epiphany: {epiphany}

Current phase: {self.current_phase}

Revelations should explore implications, mechanisms, and applications.
List each revelation on a new line, starting with "Revelation:".
"""

    def _build_aha_prompt(self, revelation: str, context: Dict[str, Any], n: int) -> str:
        return f"""
From this revelation, extract {n} concrete, paradigm-shattering AHA moments.

Revelation: {revelation}

AHA moments should be actionable, novel, and potentially transformative.
List each AHA on a new line, starting with "AHA:".
"""

    def _build_synthesis_prompt(self, epiphanies: List[str], revelations: List[str],
                                 ahas: List[str], context: Dict[str, Any]) -> str:
        epi_str = "\n".join(f"- {e}" for e in epiphanies)
        rev_str = "\n".join(f"- {r}" for r in revelations)
        aha_str = "\n".join(f"- {a}" for a in ahas)

        return f"""
Synthesize the following insights into a single, coherent, novel proposal for HelixHive.

Top Epiphanies:
{epi_str}

Top Revelations:
{rev_str}

Top AHA Moments:
{aha_str}

Current phase: {self.current_phase}

Output a JSON object with these fields:
- summary: a one-sentence summary of the proposal
- details: a paragraph describing the proposal
- novelty_score: float 0-1
- coherence_score: float 0-1
- impact_score: float 0-1
- feasibility_score: float 0-1
- implementation_steps: list of strings

Only output JSON, no other text.
"""

    # ----------------------------------------------------------------------
    # Parsing helpers
    # ----------------------------------------------------------------------

    def _parse_list_response(self, response: str, expected: int) -> List[str]:
        """Parse LLM response into a list of strings."""
        lines = response.strip().split('\n')
        items = []
        for line in lines:
            line = line.strip()
            if line and (line.startswith(('Epiphany:', 'Revelation:', 'AHA:'))):
                # Remove prefix
                parts = line.split(':', 1)
                if len(parts) > 1:
                    items.append(parts[1].strip())
                else:
                    items.append(line)
            elif line and not items:
                # If no prefix, assume first line is item
                items.append(line)
        # If we didn't get enough, pad with placeholders
        while len(items) < expected:
            items.append(f"Generated insight {len(items)+1}")
        return items[:expected]

    def _parse_proposal_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON proposal from LLM."""
        try:
            # Find JSON block
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                raise ValueError("No JSON found")
        except Exception as e:
            logger.error(f"Failed to parse proposal JSON: {e}")
            # Fallback
            return {
                'summary': 'Failed to parse proposal',
                'details': response[:200],
                'novelty_score': 0.5,
                'coherence_score': 0.5,
                'impact_score': 0.5,
                'feasibility_score': 0.5,
                'implementation_steps': []
            }
