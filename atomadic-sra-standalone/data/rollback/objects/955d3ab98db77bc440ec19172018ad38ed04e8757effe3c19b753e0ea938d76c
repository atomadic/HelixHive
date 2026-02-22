
from src.agents.luminary_base import LuminaryBase
from src.core.ollama_service import OllamaService
from src.core.evolution_vault import EvolutionVault
import json
import time
import hashlib

class OpportunityEngine(LuminaryBase):
    """
    Opportunity Engine
    Generates high-value strategic opportunities based on system state,
    market analysis, and technology trends. Each opportunity is evaluated
    through the Profit Efficiency Optimizer before logging.
    """
    def __init__(self, name="OpportunityEngine"):
        super().__init__(name)
        self.llm = OllamaService()
        self.vault = EvolutionVault()
        self.opportunities = []

    def generate_opportunity(self, context="General system expansion"):
        """Generate a strategic Opportunity Alert."""
        print(f"[{self.name}] Ideating opportunity for: {context}")

        prompt = (
            f"Generate a strategic 'Opportunity Alert' for an autonomous AI system. "
            f"Context: {context}. "
            "Format as JSON with keys: title, summary, market_eval, technical_feasibility, "
            "financial_projection, recommendation. "
            "Ensure the output is valid JSON."
        )

        response = self.llm.generate_completion(prompt)
        opportunity = None

        if response:
            try:
                response = response.replace("```json", "").replace("```", "").strip()
                opportunity = json.loads(response)
            except json.JSONDecodeError:
                print(f"[{self.name}] JSON parse failed, using fallback")

        if not opportunity:
            opportunity = self._generate_fallback(context)

        # Enrich
        opportunity["id"] = f"OA-{hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]}"
        opportunity["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        opportunity["context"] = context
        opportunity["profit_score"] = self._profit_efficiency(opportunity)
        opportunity["coherence_score"] = self._score_coherence(opportunity)
        opportunity["alignment_score"] = self._score_alignment(opportunity)

        self.opportunities.append(opportunity)
        self.vault.log_item("opportunities", opportunity)

        print(f"[{self.name}] Alert {opportunity['id']}: {opportunity.get('title', 'Untitled')} "
              f"(profit={opportunity['profit_score']:.2f})")
        return opportunity

    def scan_market(self, domains=None):
        """Scan multiple domains for opportunities."""
        if domains is None:
            domains = ["developer_tools", "ai_automation", "code_intelligence", "enterprise_devops"]
        
        results = []
        for domain in domains:
            opp = self.generate_opportunity(f"Market opportunity in {domain}")
            results.append(opp)
        
        # Sort by profit score
        return sorted(results, key=lambda o: o.get("profit_score", 0), reverse=True)

    def _generate_fallback(self, context):
        """Deterministic fallback when LLM is unavailable."""
        templates = [
            {"title": "AI-Powered Code Audit SaaS", "summary": f"Enterprise code audit platform leveraging {context}", "market_eval": {"size": "$2.1B", "growth": "18%", "target": ["Enterprise", "Fintech"]}, "technical_feasibility": {"trl": 6, "effort": "Medium"}, "financial_projection": {"revenue_model": "SaaS subscription", "roi": "340%"}, "recommendation": "Develop"},
            {"title": "Autonomous DevOps Agent", "summary": f"Self-healing CI/CD agent based on {context}", "market_eval": {"size": "$4.5B", "growth": "22%", "target": ["DevOps teams", "Cloud-native"]}, "technical_feasibility": {"trl": 5, "effort": "High"}, "financial_projection": {"revenue_model": "Usage-based", "roi": "280%"}, "recommendation": "Develop"},
            {"title": "Knowledge Graph Platform", "summary": f"Enterprise knowledge management via {context}", "market_eval": {"size": "$1.8B", "growth": "15%", "target": ["Enterprise", "Research"]}, "technical_feasibility": {"trl": 7, "effort": "Medium"}, "financial_projection": {"revenue_model": "License + SaaS", "roi": "420%"}, "recommendation": "Develop"},
        ]
        return templates[hash(context) % len(templates)]

    def _profit_efficiency(self, opp):
        """Score profit efficiency: high profit / low effort."""
        effort_map = {"Low": 0.3, "Medium": 0.6, "High": 0.9}
        feasibility = opp.get("technical_feasibility", {})
        effort_str = feasibility.get("effort", "Medium") if isinstance(feasibility, dict) else "Medium"
        effort = effort_map.get(effort_str, 0.6)
        trl = feasibility.get("trl", 5) if isinstance(feasibility, dict) else 5
        return round((trl / 9) * (1 - effort * 0.5), 4)

    def _score_coherence(self, opp):
        text = json.dumps(opp)
        return round(min(1.0, 0.6 + len(text) / 2000), 4)

    def _score_alignment(self, opp):
        keywords = ["autonomous", "ai", "code", "developer", "enterprise", "self"]
        text = json.dumps(opp).lower()
        hits = sum(1 for k in keywords if k in text)
        return round(min(1.0, 0.4 + hits * 0.1), 4)

    def get_top_opportunities(self, n=5):
        return sorted(self.opportunities, key=lambda o: o.get("profit_score", 0), reverse=True)[:n]
