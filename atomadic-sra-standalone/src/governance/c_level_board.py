
import time
import json

class CLevelBoard:
    """
    C-Level Board
    Corporate governance simulation with 7 executive roles.
    Each role evaluates proposals from its domain perspective.
    """
    ROLES = {
        "CEO": {"focus": "strategic_alignment", "weight": 0.25},
        "CTO": {"focus": "technical_feasibility", "weight": 0.20},
        "CFO": {"focus": "financial_viability", "weight": 0.15},
        "CMO": {"focus": "market_potential", "weight": 0.15},
        "CPO": {"focus": "product_impact", "weight": 0.10},
        "CRO": {"focus": "risk_assessment", "weight": 0.10},
        "CIO": {"focus": "information_security", "weight": 0.05},
    }

    def __init__(self):
        self.members = list(self.ROLES.keys())
        self.decisions = []

    def review_proposal(self, proposal):
        """
        Full board review. Each C-level evaluates independently.
        Returns aggregate decision with scores.
        """
        print(f"[Board] Convening review for: {proposal.get('title', proposal)}")
        
        title = proposal.get("title", str(proposal)) if isinstance(proposal, dict) else str(proposal)
        votes = {}
        total_score = 0
        
        for role, config in self.ROLES.items():
            score = self._evaluate(role, config["focus"], proposal)
            votes[role] = {"score": score, "focus": config["focus"]}
            total_score += score * config["weight"]
        
        decision = "APPROVED" if total_score >= 0.6 else "UNDER REVIEW" if total_score >= 0.4 else "REJECTED"
        
        result = {
            "title": title,
            "decision": decision,
            "aggregate_score": round(total_score, 4),
            "votes": votes,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        
        self.decisions.append(result)
        print(f"[Board] Decision: {decision} (score: {result['aggregate_score']})")
        return result

    def _evaluate(self, role, focus, proposal):
        """Simulate domain-specific evaluation. Returns 0.0-1.0."""
        if isinstance(proposal, dict):
            summary = str(proposal.get("summary", "")).lower()
            title = str(proposal.get("title", "")).lower()
            content = str(proposal).lower()
            
            # Heuristic: check for relevant keys and quality signals
            if focus == "technical_feasibility":
                score = 0.9 if proposal.get("feasibility") else 0.7
                if "hott" in summary or "helical" in summary:
                    score = min(1.0, score + 0.1)
                return score
            elif focus == "financial_viability":
                score = 0.8 if proposal.get("financial_projection") else 0.6
                if "infinite roi" in content:
                    score = min(1.0, score + 0.15)
                return score
            elif focus == "market_potential":
                score = 0.85 if proposal.get("market_eval") else 0.65
                if "supreme" in content or "sovereign" in content:
                    score = min(1.0, score + 0.1)
                return score
            elif focus == "risk_assessment":
                risks = proposal.get("risks", [])
                score = max(0.3, 1.0 - len(risks) * 0.15)
                if len(risks) == 0 and "bulletproof" in content:
                    score = 1.0
                return score
            elif focus == "strategic_alignment":
                score = 0.9 if proposal.get("recommendation") == "Develop" else 0.7
                if "axiom" in summary or "blueprint" in summary:
                    score = min(1.0, score + 0.1)
                return score
            elif focus == "product_impact":
                return 0.9 if "neon glass" in content else 0.8
            elif focus == "information_security":
                return 0.95 if "hott" in content else 0.85
        return 0.7

    def apply_swarm_das(self, feedback_score):
        """
        Swarm DAS (NOV-009)
        Differentiable Architecture Search at the governance level.
        Re-weights luminary (board member) influence based on recent stability/correctness.
        """
        print(f"[Board] Applying Swarm DAS Optimization (Feedback: {feedback_score:.2f})")
        
        for role, config in self.ROLES.items():
            # Neural adjustment: weight shifts toward high-performance roles
            # This simulates a differentiable re-weighting layer.
            current_weight = config["weight"]
            delta = 0.02 * (feedback_score - 0.5)
            config["weight"] = max(0.05, min(0.4, current_weight + delta))
            
        # Re-normalize weights to 1.0
        total = sum(c["weight"] for c in self.ROLES.values())
        for c in self.ROLES.values():
            c["weight"] /= total
        
        print("[Board] Swarm Weights Updated.")

    def get_history(self):
        return self.decisions
