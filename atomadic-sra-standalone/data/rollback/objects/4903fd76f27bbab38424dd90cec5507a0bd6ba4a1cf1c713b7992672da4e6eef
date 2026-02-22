
import time
import json

class MonetizationOracle:
    """
    Monetization Oracle
    Evaluates opportunities for revenue potential and generates
    commercialization paths with financial projections.
    """
    REVENUE_MODELS = ["subscription", "usage_based", "freemium", "enterprise_license", "marketplace", "api_access"]

    def __init__(self):
        self.plans = []

    def generate_revenue_plan(self, opportunity):
        """
        Analyze opportunity and generate a revenue plan.
        """
        title = opportunity.get("title", str(opportunity)) if isinstance(opportunity, dict) else str(opportunity)
        print(f"[Oracle] Analyzing monetization for: {title}")
        
        # Score each revenue model
        model_scores = {}
        for model in self.REVENUE_MODELS:
            model_scores[model] = self._score_model(model, opportunity)
        
        best_model = max(model_scores, key=model_scores.get)
        
        plan = {
            "opportunity": title,
            "recommended_model": best_model,
            "model_scores": model_scores,
            "projected_revenue": self._project_revenue(best_model, opportunity),
            "time_to_market": self._estimate_ttm(opportunity),
            "risk_level": self._assess_risk(opportunity),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        
        self.plans.append(plan)
        print(f"[Oracle] Recommended: {best_model} (projected: {plan['projected_revenue']})")
        return plan

    def _score_model(self, model, opportunity):
        """Heuristic scoring for revenue model fit."""
        base = 0.5
        if isinstance(opportunity, dict):
            if model == "subscription" and "IDE" in str(opportunity):
                base = 0.85
            elif model == "api_access" and "engine" in str(opportunity).lower():
                base = 0.80
            elif model == "enterprise_license" and "enterprise" in str(opportunity).lower():
                base = 0.90
            elif model == "freemium":
                base = 0.70
            elif model == "marketplace":
                base = 0.65
            elif model == "usage_based":
                base = 0.75
        return round(base, 2)

    def _project_revenue(self, model, opportunity):
        """Simple revenue projection."""
        projections = {
            "subscription": "$50K-200K ARR",
            "usage_based": "$30K-150K ARR",
            "freemium": "$20K-100K ARR",
            "enterprise_license": "$100K-500K ARR",
            "marketplace": "$15K-80K ARR",
            "api_access": "$40K-180K ARR"
        }
        return projections.get(model, "Unknown")

    def _estimate_ttm(self, opportunity):
        """Estimate time to market."""
        if isinstance(opportunity, dict):
            effort = str(opportunity.get("effort", "Medium")).lower()
            if "low" in effort:
                return "1-2 months"
            elif "high" in effort:
                return "6-12 months"
        return "3-6 months"

    def _assess_risk(self, opportunity):
        """Risk assessment."""
        if isinstance(opportunity, dict) and len(opportunity.get("risks", [])) > 2:
            return "HIGH"
        return "LOW"

    def get_plans(self):
        return self.plans
