import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.governance.c_level_board import CLevelBoard
import json

def run_expert_review():
    board = CLevelBoard()
    
    # Proposal: Final Deployment Readiness of SRA v3.2.1.0
    proposal = {
        "title": "SRA v3.2.1.0 Standalone Flight Readiness",
        "summary": "Full audit complete. Core logic infused with helical derivations. Blueprint verified. Agent swarm online.",
        "feasibility": True,
        "market_eval": "High (Atomadic Sovereign Tier)",
        "financial_projection": "Maximal ROI via self-evolution",
        "risks": ["Model drift", "Entropy accumulation"],
        "recommendation": "Develop"
    }
    
    review_result = board.review_proposal(proposal)
    
    # Proposal: Neon Glass UI Overhaul
    ui_proposal = {
        "title": "Neon Glass UI/UX Sovereign Overhaul",
        "summary": "Implementation of vibrant, translucent, glassmorphism-based interface with micro-animations and Inter typography.",
        "feasibility": True,
        "market_eval": "Premium UX differentiation",
        "financial_projection": "Increased user retention and brand value",
        "risks": ["Performance overhead on local LLM"],
        "recommendation": "Develop"
    }
    
    ui_result = board.review_proposal(ui_proposal)
    
    print("\n" + "="*50)
    print("FINAL EXPERT PANEL REVIEW SUMMARY")
    print("="*50)
    print(f"Readiness Score: {review_result['aggregate_score']}")
    print(f"Readiness Decision: {review_result['decision']}")
    print("-" * 30)
    print(f"UI/UX Score: {ui_result['aggregate_score']}")
    print(f"UI/UX Decision: {ui_result['decision']}")
    print("="*50)

if __name__ == "__main__":
    run_expert_review()
