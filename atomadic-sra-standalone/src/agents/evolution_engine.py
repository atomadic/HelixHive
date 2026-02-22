
from src.agents.luminary_base import LuminaryBase
from src.core.ollama_service import OllamaService
from src.core.evolution_vault import EvolutionVault
import json
import time
import hashlib

class EvolutionEngine(LuminaryBase):
    """
    Evolution Engine
    Proposes and evaluates architectural upgrades for Recursive Self-Improvement (RSI).
    Maintains an evolution history and tracks which upgrades have been applied.
    """
    def __init__(self, name="EvolutionEngine", force_offline=False):
        super().__init__(name)
        self.llm = OllamaService(force_offline=force_offline)
        self.vault = EvolutionVault()
        self.evolution_history = []
        self.applied_upgrades = []

    def propose_evolution(self, focus_area="Architecture"):
        """Propose an evolutionary upgrade for the SRA system."""
        print(f"[{self.name}] Designing evolution for: {focus_area}")

        prompt = (
            f"Propose an evolutionary upgrade for the SRA (Supreme Research Agent) system. "
            f"Focus Area: {focus_area}. "
            "Format as JSON with keys: title, summary, impact_assessment, feasibility, next_steps. "
            "Ensure the output is valid JSON."
        )

        response = self.llm.generate_completion(prompt)
        evolution = None

        if response:
            try:
                response = response.replace("```json", "").replace("```", "").strip()
                evolution = json.loads(response)
            except json.JSONDecodeError:
                print(f"[{self.name}] JSON parse failed, using fallback")

        if not evolution:
            evolution = self._generate_fallback(focus_area)

        # Enrich
        evolution["id"] = f"EV-{hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]}"
        evolution["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        evolution["focus_area"] = focus_area
        evolution["status"] = "proposed"
        evolution["risk_score"] = self._assess_risk(evolution)
        evolution["priority"] = self._prioritize(evolution)

        self.evolution_history.append(evolution)
        self.vault.log_item("evolutions", evolution)

        print(f"[{self.name}] Evolution {evolution['id']}: {evolution.get('title', 'Untitled')} "
              f"(priority={evolution['priority']}, risk={evolution['risk_score']:.2f})")
        return evolution

    def apply_upgrade(self, evolution_id):
        """Mark an evolution as applied (simulated application)."""
        for ev in self.evolution_history:
            if ev["id"] == evolution_id:
                ev["status"] = "applied"
                ev["applied_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                self.applied_upgrades.append(ev)
                print(f"[{self.name}] Applied: {ev['title']}")
                return ev
        return None

    def roadmap(self, num_proposals=5):
        """Generate a prioritized evolution roadmap."""
        areas = ["Architecture", "Performance", "Security", "UX", "Intelligence",
                 "Scalability", "Resilience", "Observability"]
        
        proposals = []
        for area in areas[:num_proposals]:
            proposals.append(self.propose_evolution(area))
        
        return sorted(proposals, key=lambda p: p.get("priority", 99))

    def _generate_fallback(self, focus_area):
        templates = {
            "Architecture": {"title": "Microkernel Agent Architecture", "summary": "Refactor monolithic agents into a microkernel pattern with hot-swappable plugins", "impact_assessment": {"stability": "+40%", "flexibility": "+60%"}, "feasibility": {"effort": "High", "risk": "Medium"}, "next_steps": ["Design plugin API", "Implement kernel", "Migrate agents"]},
            "Performance": {"title": "Async Pipeline Engine", "summary": "Replace synchronous agent pipeline with fully async event-driven architecture", "impact_assessment": {"throughput": "+300%", "latency": "-60%"}, "feasibility": {"effort": "Medium", "risk": "Low"}, "next_steps": ["Add asyncio", "Convert agents", "Benchmark"]},
            "Security": {"title": "Zero-Trust Agent Communication", "summary": "Implement mTLS and signed message envelopes between all agents", "impact_assessment": {"security": "+80%", "trust": "+50%"}, "feasibility": {"effort": "Medium", "risk": "Low"}, "next_steps": ["Generate certs", "Implement signing", "Add verification"]},
            "UX": {"title": "Real-time Agent Dashboard", "summary": "WebSocket-powered live dashboard showing agent states, metrics, and logs", "impact_assessment": {"usability": "+70%", "observability": "+50%"}, "feasibility": {"effort": "Medium", "risk": "Low"}, "next_steps": ["Add WebSocket", "Build React UI", "Connect metrics"]},
            "Intelligence": {"title": "Multi-Model Ensemble Reasoning", "summary": "Combine outputs from multiple LLMs via weighted voting for higher accuracy", "impact_assessment": {"accuracy": "+25%", "reliability": "+40%"}, "feasibility": {"effort": "High", "risk": "Medium"}, "next_steps": ["Add model router", "Implement voting", "Calibrate weights"]},
        }
        return templates.get(focus_area, templates["Architecture"])

    def _assess_risk(self, evolution):
        """Assess risk score (0.0 = safe, 1.0 = dangerous)."""
        feasibility = evolution.get("feasibility", {})
        risk_str = feasibility.get("risk", "Medium") if isinstance(feasibility, dict) else "Medium"
        effort_str = feasibility.get("effort", "Medium") if isinstance(feasibility, dict) else "Medium"
        risk_map = {"Low": 0.2, "Medium": 0.5, "High": 0.8}
        effort_map = {"Low": 0.1, "Medium": 0.3, "High": 0.5}
        return round(risk_map.get(risk_str, 0.5) * 0.6 + effort_map.get(effort_str, 0.3) * 0.4, 4)

    def _prioritize(self, evolution):
        """Assign priority (1=highest). Lower risk + higher impact -> higher priority."""
        risk = evolution.get("risk_score", 0.5)
        # More text in impact = higher impact
        impact_text = json.dumps(evolution.get("impact_assessment", {}))
        impact = min(1.0, len(impact_text) / 200)
        score = impact * (1 - risk)
        if score > 0.5:
            return 1
        elif score > 0.3:
            return 2
        else:
            return 3

    def get_history(self):
        return self.evolution_history

    def get_applied(self):
        return self.applied_upgrades
