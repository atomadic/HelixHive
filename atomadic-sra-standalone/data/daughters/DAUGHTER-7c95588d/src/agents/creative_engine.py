
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.core.ollama_service import OllamaService

class CreativeFeatureEngine:
    """
    Creative Feature Engine
    Brainstorms, evaluates, and plans new features for the SRA platform.
    """
    def __init__(self):
        self.llm = OllamaService()
        self.proposals = []
        self.approved = []

    def brainstorm(self, context="SRA IDE Platform"):
        """Phase 1: Think -- Brainstorm new feature ideas."""
        print(f"[Creative] Brainstorming for: {context}")
        
        prompt = (
            f"You are an AI product innovator. Brainstorm 5 novel feature ideas for: {context}\n"
            "For each feature, provide:\n"
            "- Name\n"
            "- One-line description\n"
            "- Impact (Low/Medium/High)\n"
            "- Effort (Low/Medium/High)\n"
            "Format as a numbered list."
        )
        
        result = self.llm.generate_completion(prompt)
        if result:
            print(f"[Creative] Generated ideas:\n{result[:500]}")
            return result
        return self._fallback_ideas(context)

    def analyze(self, idea):
        """Phase 2: Analyze -- Deep analysis of a feature idea."""
        print(f"[Creative] Analyzing: {idea[:60]}...")
        
        prompt = (
            f"Analyze this feature idea for a developer IDE platform:\n{idea}\n\n"
            "Provide:\n"
            "1. Technical feasibility assessment\n"
            "2. Required components/dependencies\n"
            "3. Integration points with existing system\n"
            "4. Risk factors\n"
            "5. Estimated development time"
        )
        
        result = self.llm.generate_completion(prompt)
        return result or "Analysis pending -- LLM unavailable"

    def propose(self, idea, analysis):
        """Phase 3: Propose -- Create formal proposal."""
        proposal = {
            "id": f"FP-{len(self.proposals):04d}",
            "idea": idea,
            "analysis": str(analysis)[:500],
            "status": "proposed",
            "votes": {},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        self.proposals.append(proposal)
        print(f"[Creative] Proposal created: {proposal['id']}")
        return proposal

    def council_review(self, proposal):
        """Phase 4: Council -- Multi-perspective review."""
        from src.governance.c_level_board import CLevelBoard
        board = CLevelBoard()
        
        review = board.review_proposal({
            "title": proposal.get("idea", "")[:100],
            "recommendation": "Develop",
            "feasibility": True
        })
        
        proposal["votes"] = review.get("votes", {})
        proposal["council_score"] = review.get("aggregate_score", 0)
        proposal["council_decision"] = review.get("decision", "UNDER REVIEW")
        
        print(f"[Creative] Council: {review['decision']} (score={review['aggregate_score']})")
        return review

    def refine(self, proposal):
        """Phase 5: Refine -- Improve based on council feedback."""
        if proposal.get("council_decision") == "REJECTED":
            proposal["status"] = "rejected"
            return proposal
        
        # Use LLM to refine based on feedback
        prompt = (
            f"Refine this feature proposal based on board feedback:\n"
            f"Original: {proposal['idea']}\n"
            f"Score: {proposal.get('council_score', 'N/A')}\n"
            f"Decision: {proposal.get('council_decision', 'N/A')}\n\n"
            "Provide an improved version that addresses any concerns."
        )
        
        refinement = self.llm.generate_completion(prompt)
        if refinement:
            proposal["refined_idea"] = refinement[:500]
        
        proposal["status"] = "refined"
        return proposal

    def plan(self, proposal):
        """Phase 6: Plan -- Create implementation plan."""
        plan = {
            "proposal_id": proposal["id"],
            "tasks": [
                f"1. Design {proposal['idea'][:50]} architecture",
                f"2. Implement core logic",
                f"3. Add API endpoints",
                f"4. Build UI components",
                f"5. Write tests",
                f"6. Integration testing",
                f"7. Deploy and verify"
            ],
            "estimated_effort": "Medium",
            "priority": "P1" if proposal.get("council_score", 0) > 0.7 else "P2"
        }
        
        proposal["plan"] = plan
        proposal["status"] = "planned"
        
        if proposal.get("council_decision") == "APPROVED":
            self.approved.append(proposal)
        
        print(f"[Creative] Plan created: {len(plan['tasks'])} tasks, priority={plan['priority']}")
        return plan


    def _fallback_ideas(self, context):
        """Fallback when LLM is unavailable."""
        return (
            "1. Real-time Agent Collaboration Dashboard -- Live view of agent interactions (High/Medium)\n"
            "2. Automated Code Review Pipeline -- AI-powered code review with style enforcement (High/Medium)\n"
            "3. Knowledge Graph Visualizer -- Interactive 3D knowledge map (Medium/High)\n"
            "4. Performance Regression Detector -- Automatic benchmark tracking (High/Low)\n"
            "5. Natural Language Query Interface -- Ask questions about codebase in plain English (High/Medium)"
        )

    def get_proposals(self):
        return self.proposals

    def get_approved(self):
        return self.approved
