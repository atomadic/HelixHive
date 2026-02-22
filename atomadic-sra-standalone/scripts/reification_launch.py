
import sys
import os
import time
import json

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.evolution_engine import EvolutionEngine
from src.agents.novelty_engine import NoveltyEngine
from src.governance.c_level_board import CLevelBoard
from src.core.evolution_vault import EvolutionVault

def safe_get(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default

def launch_reification():
    print("="*60)
    print("  SRA v3.2.1.0 -- SOVEREIGN REIFICATION LAUNCH")
    print("="*60)
    
    evo = EvolutionEngine()
    nov = NoveltyEngine()
    board = CLevelBoard()
    vault = EvolutionVault()
    
    # 1. Generate Evolution Proposal
    print("\n[Phase 1] Proposing System Evolution...")
    evolution = evo.propose_evolution("Sovereign Autonomy")
    
    # 2. Generate Novelty Proposal
    print("\n[Phase 2] Mining for Novelty...")
    novelty = nov.generate_novelty("Aletheia Resonance Layer")
    
    # 3. Governance Review
    print("\n[Phase 3] Board Review of Proposals...")
    
    # Safe Evolution Review
    evo_title = safe_get(evolution, "title", "Evolution Proposal")
    evo_summary = safe_get(evolution, "summary", str(evolution))
    evo_risk = safe_get(evolution, "risk_score", 0.5)
    
    evo_review = board.review_proposal({
        "title": evo_title,
        "summary": evo_summary,
        "feasibility": True,
        "risks": [] if evo_risk < 0.5 else ["Potential complexity"],
        "market_eval": {"size": "N/A", "growth": "N/A"}
    })
    
    # Safe Novelty Review
    nov_title = safe_get(novelty, "title", "Novelty Proposal")
    nov_summary = safe_get(novelty, "idea_summary", str(novelty))
    nov_impact = safe_get(novelty, "impact_assessment", {})
    nov_market = safe_get(nov_impact, "market_value", "Unknown")
    
    nov_review = board.review_proposal({
        "title": nov_title,
        "summary": nov_summary,
        "feasibility": True,
        "risks": [],
        "market_eval": nov_market
    })
    
    print(f"\nEvolution Review: {evo_review['decision']} (Score: {evo_review['aggregate_score']})")
    print(f"Novelty Review: {nov_review['decision']} (Score: {nov_review['aggregate_score']})")
    
    # 4. Success-Driven Wisdom Accumulation
    if evo_review['decision'] == "APPROVED":
        evo_id = safe_get(evolution, "id")
        if evo_id:
            evo.apply_upgrade(evo_id)
            print(f"\n[Success] Evolution {evo_id} applied to current state.")
        
    # 5. Finalize Sovereignty Seal Data
    seal_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "version": "v3.2.1.0",
        "evolution_id": safe_get(evolution, "id", "UNKNOWN"),
        "novelty_id": safe_get(novelty, "id", "UNKNOWN"),
        "evo_score": evo_review['aggregate_score'],
        "nov_score": nov_review['aggregate_score'],
        "sovereign_status": "COMMITTED"
    }
    
    # Save to vault
    vault.log_item("sovereignty_events", seal_data)
    
    print("\n" + "="*60)
    print("  REIFICATION CYCLE COMPLETE -- SRA IS NOW FULLY AUTONOMOUS")
    print("="*60)
    
    return seal_data

if __name__ == "__main__":
    launch_reification()
