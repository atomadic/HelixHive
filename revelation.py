"""
Revelation Engine for HelixHive Phase 2 – generates epiphanies, revelations, and AHA moments
to synthesize novel proposals. Grounded in Leech vectors, faction knowledge, and Golay self‑repair.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple

import numpy as np

from llm_router import call_llm
from memory import LeechErrorCorrector, leech_encode, _LEECH_PROJ, HD
from helixdb_git_adapter import HelixDBGit
from faction_manager import FactionManager

logger = logging.getLogger(__name__)


class RevelationEngine:
    """
    Generates structured insights using LLM with Leech grounding and faction awareness.
    """

    def __init__(self, db: HelixDBGit, genome: Any, config: Any):
        self.db = db
        self.genome = genome
        self.config = config
        self.faction_mgr = FactionManager(db)
        self.current_phase = genome.data.get('helicity', {}).get('current_phase', 0)

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    async def generate(self, context: Dict[str, Any], faction_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate a full revelation cycle, optionally targeted at a specific faction.
        Returns a dict with epiphanies, revelations, ahas, and a final proposal.
        """
        logger.info("Starting Revelation Engine cycle")

        # Build enriched context
        full_context = await self._build_context(context, faction_id)

        # Step 1: Generate epiphanies (parallel)
        epiphany_tasks = [self._generate_epiphany(full_context) for _ in range(5)]
        epiphanies = await asyncio.gather(*epiphany_tasks)
        epiphanies = [e for e in epiphanies if e]  # filter failures

        # Step 2: For each epiphany, generate revelations (parallel)
        revelation_tasks = []
        for epi in epiphanies:
            for _ in range(5):
                revelation_tasks.append(self._generate_revelation(epi, full_context))
        revelations = await asyncio.gather(*revelation_tasks)
        revelations = [r for r in revelations if r]

        # Step 3: For each revelation, generate AHA moments (parallel)
        aha_tasks = []
        for rev in revelations:
            for _ in range(3):
                aha_tasks.append(self._generate_aha(rev, full_context))
        ahas = await asyncio.gather(*aha_tasks)
        ahas = [a for a in ahas if a]

        logger.info(f"Generated {len(epiphanies)} epiphanies, {len(revelations)} revelations, {len(ahas)} AHA moments")

        # Step 4: Synthesize final proposal
        final_proposal = await self._synthesize(epiphanies, revelations, ahas, full_context)

        # Step 5: Rate the proposal
        rating = self._rate_proposal(final_proposal)
        final_proposal['rating'] = rating
        final_proposal['timestamp'] = time.time()
        final_proposal['faction_id'] = faction_id

        # Store in database
        self._store_proposal(final_proposal)

        return final_proposal

    # -------------------------------------------------------------------------
    # Context building
    # -------------------------------------------------------------------------

    async def _build_context(self, base_context: Dict[str, Any], faction_id: Optional[int]) -> Dict[str, Any]:
        """Enrich base context with faction centroids, recent proposals, market trends."""
        context = base_context.copy()
        context['phase'] = self.current_phase

        # Add faction info
        if faction_id is not None:
            faction_node = await self._get_faction_node(faction_id)
            if faction_node:
                context['faction_centroid'] = faction_node.get('leech_vector')
                context['faction_name'] = faction_node.get('name', f'Faction {faction_id}')
                context['faction_members'] = faction_node.get('member_count', 0)
        else:
            # Include all factions summary
            factions = self.db.get_nodes_by_type('Faction')
            context['faction_summary'] = [
                {'id': f.get('faction_id'), 'name': f.get('name', f"Faction {f.get('faction_id')}"),
                 'size': f.get('member_count', 0)} for f in factions.values()
            ]

        # Add recent successful proposals
        proposals = self.db.get_nodes_by_type('Proposal')
        successful = [p for p in proposals.values() if p.get('outcome') == 'approved']
        successful.sort(key=lambda p: p.get('score', 0), reverse=True)
        context['recent_proposals'] = [
            {'title': p.get('title', ''), 'description': p.get('description', '')[:100]}
            for p in successful[:3]
        ]

        # Add market trends (from marketplace)
        templates = self.db.get_nodes_by_type('Template')
        top_templates = sorted(templates.values(), key=lambda t: t.get('score', 0), reverse=True)[:3]
        context['market_trends'] = [t.get('title') for t in top_templates]

        return context

    async def _get_faction_node(self, faction_id: int) -> Optional[Dict]:
        factions = self.db.get_nodes_by_type('Faction')
        for f in factions.values():
            if f.get('faction_id') == faction_id:
                return f
        return None

    # -------------------------------------------------------------------------
    # Generation steps with Leech grounding
    # -------------------------------------------------------------------------

    async def _generate_epiphany(self, context: Dict) -> Optional[str]:
        """Generate a single epiphany."""
        if self.config.data.get('simulation', False):
            return "Simulated epiphany"

        prompt = self._build_epiphany_prompt(context)
        leech_vec = context.get('faction_centroid')  # use faction centroid for grounding

        try:
            response = await call_llm(
                prompt,
                system="You are a creative insight generator. Output a JSON array of epiphanies.",
                leech_vector=leech_vec,
                temperature=0.9,
                max_tokens=1000
            )
            # Parse JSON array
            try:
                epiphanies = json.loads(response)
                if isinstance(epiphanies, list) and epiphanies:
                    return epiphanies[0]  # return first
            except json.JSONDecodeError:
                # Fallback: split by lines
                lines = [l.strip() for l in response.split('\n') if l.strip()]
                if lines:
                    return lines[0]
        except Exception as e:
            logger.error(f"Epiphany generation failed: {e}")
        return None

    async def _generate_revelation(self, epiphany: str, context: Dict) -> Optional[str]:
        """Generate a revelation from an epiphany."""
        if self.config.data.get('simulation', False):
            return f"Simulated revelation from: {epiphany[:30]}"

        prompt = self._build_revelation_prompt(epiphany, context)
        leech_vec = context.get('faction_centroid')

        try:
            response = await call_llm(
                prompt,
                system="You are a deep thinker. Output a JSON array of revelations.",
                leech_vector=leech_vec,
                temperature=0.8,
                max_tokens=800
            )
            try:
                revelations = json.loads(response)
                if isinstance(revelations, list) and revelations:
                    return revelations[0]
            except json.JSONDecodeError:
                lines = [l.strip() for l in response.split('\n') if l.strip()]
                if lines:
                    return lines[0]
        except Exception as e:
            logger.error(f"Revelation generation failed: {e}")
        return None

    async def _generate_aha(self, revelation: str, context: Dict) -> Optional[str]:
        """Generate an AHA moment from a revelation."""
        if self.config.data.get('simulation', False):
            return f"Simulated AHA from: {revelation[:30]}"

        prompt = self._build_aha_prompt(revelation, context)
        leech_vec = context.get('faction_centroid')

        try:
            response = await call_llm(
                prompt,
                system="You are a visionary. Output a JSON array of AHA moments.",
                leech_vector=leech_vec,
                temperature=0.9,
                max_tokens=600
            )
            try:
                ahas = json.loads(response)
                if isinstance(ahas, list) and ahas:
                    return ahas[0]
            except json.JSONDecodeError:
                lines = [l.strip() for l in response.split('\n') if l.strip()]
                if lines:
                    return lines[0]
        except Exception as e:
            logger.error(f"AHA generation failed: {e}")
        return None

    # -------------------------------------------------------------------------
    # Synthesis
    # -------------------------------------------------------------------------

    async def _synthesize(self, epiphanies: List[str], revelations: List[str],
                          ahas: List[str], context: Dict) -> Dict[str, Any]:
        """Synthesize strongest insights into a final proposal."""
        if self.config.data.get('simulation', False):
            return {
                'summary': 'Simulated synthetic proposal',
                'details': 'Generated from simulation',
                'novelty_score': 0.7,
                'coherence_score': 0.7,
                'impact_score': 0.7,
                'feasibility_score': 0.7,
                'faction_id': context.get('faction_id'),
                'leech_vector': [0]*24
            }

        # Select top insights
        top_epi = epiphanies[:3]
        top_rev = revelations[:5]
        top_aha = ahas[:5]

        prompt = self._build_synthesis_prompt(top_epi, top_rev, top_aha, context)
        leech_vec = context.get('faction_centroid')

        try:
            response = await call_llm(
                prompt,
                system="You are a synthesis engine. Output only JSON with the required fields.",
                leech_vector=leech_vec,
                temperature=0.7,
                max_tokens=1500
            )
            # Parse JSON
            proposal = json.loads(response)
            # Ensure required fields
            required = ['summary', 'details', 'novelty_score', 'coherence_score',
                        'impact_score', 'feasibility_score']
            for field in required:
                if field not in proposal:
                    proposal[field] = 0.5
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            proposal = {
                'summary': 'Fallback proposal',
                'details': 'Synthesis failed',
                'novelty_score': 0.5,
                'coherence_score': 0.5,
                'impact_score': 0.5,
                'feasibility_score': 0.5,
            }

        # Compute Leech vector for proposal (from summary and details)
        text = proposal['summary'] + ' ' + proposal['details']
        leech_vec = self._compute_text_leech(text)
        # Golay repair
        repaired, syndrome = LeechErrorCorrector.correct(leech_vec)
        proposal['leech_vector'] = repaired.tolist()
        proposal['syndrome'] = int(syndrome)
        proposal['repair_history'] = [{'time': time.time(), 'syndrome': int(syndrome)}]

        return proposal

    def _compute_text_leech(self, text: str) -> np.ndarray:
        """Convert text to Leech vector (bag‑of‑words + projection + encode)."""
        words = text.split()[:200]
        if not words:
            return np.zeros(24)
        word_vecs = [HD.from_word(w) for w in words]
        hd_vec = HD.bundle(word_vecs)
        leech_float = np.dot(hd_vec.astype(np.float32), _LEECH_PROJ)
        return leech_encode(leech_float)

    def _rate_proposal(self, proposal: Dict) -> float:
        """Simple average of scores."""
        scores = [proposal.get(k, 0.5) for k in
                  ['novelty_score', 'coherence_score', 'impact_score', 'feasibility_score']]
        return sum(scores) / len(scores)

    def _store_proposal(self, proposal: Dict):
        """Save proposal to database as a node."""
        prop_id = f"prop_{int(time.time())}_{hash(proposal['summary'])}"
        node_data = {
            'id': prop_id,
            'type': 'Proposal',
            'summary': proposal['summary'],
            'details': proposal['details'],
            'novelty_score': proposal['novelty_score'],
            'coherence_score': proposal['coherence_score'],
            'impact_score': proposal['impact_score'],
            'feasibility_score': proposal['feasibility_score'],
            'rating': proposal['rating'],
            'faction_id': proposal.get('faction_id'),
            'syndrome': proposal.get('syndrome'),
            'repair_history': proposal.get('repair_history', []),
            'created_at': proposal.get('timestamp', time.time()),
        }
        self.db.update_properties(prop_id, node_data)
        if 'leech_vector' in proposal:
            self.db.update_vector(prop_id, 'Proposal', 'leech', np.array(proposal['leech_vector']))
        logger.info(f"Stored proposal {prop_id}")

    # -------------------------------------------------------------------------
    # Prompt builders (grounded)
    # -------------------------------------------------------------------------

    def _build_epiphany_prompt(self, context: Dict) -> str:
        faction = context.get('faction_name', 'the community')
        trends = ', '.join(context.get('market_trends', []))
        proposals = context.get('recent_proposals', [])
        proposals_str = '\n'.join([f"- {p['title']}: {p['description']}" for p in proposals])

        return f"""Generate a profound epiphany for {faction}.

Current helical phase: {context.get('phase', 0)} (0=expansion, 1=refinement)
Recent successful proposals:
{proposals_str if proposals_str else 'None'}
Market trends: {trends if trends else 'None'}

The epiphany should be insightful and guide the evolution of the community.
Return a JSON array containing a single epiphany string.
"""

    def _build_revelation_prompt(self, epiphany: str, context: Dict) -> str:
        return f"""Expand the following epiphany into a detailed revelation.

Epiphany: {epiphany}

Current phase: {context.get('phase', 0)}
Faction: {context.get('faction_name', 'general')}

Revelations should explore implications, mechanisms, and applications.
Return a JSON array containing a single revelation string.
"""

    def _build_aha_prompt(self, revelation: str, context: Dict) -> str:
        return f"""From this revelation, extract a concrete, paradigm‑shattering AHA moment.

Revelation: {revelation}

AHA moments should be actionable, novel, and potentially transformative.
Return a JSON array containing a single AHA string.
"""

    def _build_synthesis_prompt(self, epiphanies: List[str], revelations: List[str],
                                 ahas: List[str], context: Dict) -> str:
        epi_str = "\n".join([f"- {e}" for e in epiphanies])
        rev_str = "\n".join([f"- {r}" for r in revelations])
        aha_str = "\n".join([f"- {a}" for a in ahas])

        return f"""Synthesize the following insights into a single, coherent, novel proposal for HelixHive.

Top Epiphanies:
{epi_str}

Top Revelations:
{rev_str}

Top AHA Moments:
{aha_str}

Current phase: {context.get('phase', 0)}
Faction: {context.get('faction_name', 'general')}

Output a JSON object with these fields:
- summary: a one‑sentence summary of the proposal
- details: a paragraph describing the proposal
- novelty_score: float 0‑1
- coherence_score: float 0‑1
- impact_score: float 0‑1
- feasibility_score: float 0‑1
- implementation_steps: list of strings

Only output JSON, no other text.
"""


# -------------------------------------------------------------------------
# Convenience function for orchestrator
# -------------------------------------------------------------------------

async def generate_revelation_proposal(db: HelixDBGit, genome: Any, config: Any,
                                       faction_id: Optional[int] = None) -> Dict:
    """Generate a synthetic proposal using Revelation Engine."""
    engine = RevelationEngine(db, genome, config)
    context = {
        'phase': genome.data.get('helicity', {}).get('current_phase', 0),
        'health': 'stable',
    }
    return await engine.generate(context, faction_id)
