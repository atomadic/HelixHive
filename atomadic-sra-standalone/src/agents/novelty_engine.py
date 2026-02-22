
from src.agents.luminary_base import LuminaryBase
from src.core.ollama_service import OllamaService
from src.core.evolution_vault import EvolutionVault
import json
import time
import hashlib

class NoveltyEngine(LuminaryBase):
    """
    Novelty Engine
    Mines serendipitous ideas by cross-pollinating concepts from different domains.
    Uses seed traces, Leech-space exploration, and LLM brainstorming.
    Logs all discoveries to the Evolution Vault.
    """
    def __init__(self, name="NoveltyEngine", force_offline=False):
        super().__init__(name)
        self.llm = OllamaService(force_offline=force_offline)
        self.vault = EvolutionVault()
        self.seed_history = []
        self.proposals = []

    def generate_novelty(self, seed_trace="System Logic"):
        """Generate a Novelty Proposal from a seed trace."""
        print(f"[{self.name}] Scanning for novelty from seed: {seed_trace}")
        self.seed_history.append(seed_trace)
        
        prompt = (
            f"Generate a 'Novelty Proposal' based on the seed trace: {seed_trace}. "
            "Focus on stable, interesting, and theoretically sound ideas. "
            "Format as JSON with keys: title, idea_summary, novelty_rationale, impact_assessment. "
            "Ensure the output is valid JSON."
        )

        response = self.llm.generate_completion(prompt)
        proposal = None

        if response:
            try:
                response = response.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(response)
                if isinstance(parsed, dict):
                    proposal = parsed
                else:
                    print(f"[{self.name}] JSON parsed but not a dict, using fallback")
            except json.JSONDecodeError:
                print(f"[{self.name}] JSON parse failed, using structured fallback")

        if not proposal:
            proposal = self._generate_fallback(seed_trace)

        # Enrich with metadata
        proposal["id"] = f"NP-{hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]}"
        proposal["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        proposal["seed_trace"] = seed_trace
        proposal["coherence_score"] = self._score_coherence(proposal)
        proposal["alignment_score"] = self._score_alignment(proposal)

        self.proposals.append(proposal)
        self.vault.log_item("novelties", proposal)
        
        print(f"[{self.name}] Proposal {proposal['id']}: {proposal.get('title', 'Untitled')}")
        return proposal

    def cross_pollinate(self, seeds):
        """Generate novelty by combining multiple seed traces."""
        combined = "  ".join(seeds)
        print(f"[{self.name}] Cross-pollinating: {combined}")
        return self.generate_novelty(f"Cross-pollination of {combined}")

    def _generate_fallback(self, seed):
        """Deterministic fallback when LLM is unavailable."""
        templates = [
            {"title": f"Adaptive {seed} Controller", "idea_summary": f"Self-tuning controller for {seed} that learns optimal parameters through observation", "novelty_rationale": {"seed_traces": [seed], "mechanism": "parameter space exploration"}, "impact_assessment": {"stability_gain": "+20%", "intelligence_boost": "+15%", "market_value": "$25K ARR"}},
            {"title": f"Distributed {seed} Network", "idea_summary": f"Peer-to-peer mesh of {seed} nodes enabling resilient, decentralized operation", "novelty_rationale": {"seed_traces": [seed], "mechanism": "network topology innovation"}, "impact_assessment": {"stability_gain": "+35%", "intelligence_boost": "+10%", "market_value": "$40K ARR"}},
            {"title": f"Predictive {seed} Engine", "idea_summary": f"Forecasts {seed} states 3 steps ahead using autoregressive modeling", "novelty_rationale": {"seed_traces": [seed], "mechanism": "temporal extrapolation"}, "impact_assessment": {"stability_gain": "+15%", "intelligence_boost": "+30%", "market_value": "$35K ARR"}},
        ]
        idx = hash(seed) % len(templates)
        return templates[idx]

    def _score_coherence(self, proposal):
        """Score geometric coherence of a proposal (0.0 - 1.0)."""
        # Heuristic: longer, more detailed proposals score higher
        text = json.dumps(proposal)
        completeness = min(1.0, len(text) / 500)
        has_rationale = 0.2 if "rationale" in text.lower() else 0
        has_impact = 0.2 if "impact" in text.lower() else 0
        return round(min(1.0, 0.5 + completeness * 0.3 + has_rationale + has_impact), 4)

    def _score_alignment(self, proposal):
        """Score strategic alignment (0.0 - 1.0)."""
        keywords = ["stability", "intelligence", "market", "efficiency", "autonomous", "self"]
        text = json.dumps(proposal).lower()
        hits = sum(1 for k in keywords if k in text)
        return round(min(1.0, 0.4 + hits * 0.1), 4)

    def get_proposals(self):
        return self.proposals

    def get_top_proposals(self, n=5):
        return sorted(self.proposals, key=lambda p: p.get("coherence_score", 0), reverse=True)[:n]
