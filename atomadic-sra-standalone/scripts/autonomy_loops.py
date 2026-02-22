
import sys
import os
import time
import json
import argparse

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

def run_loop(loop_id, force_offline=False):
    print(f"\n" + "-"*60)
    print(f"  EVOLUTION LOOP #{loop_id} (Offline={force_offline})")
    print("-"*60)
    
    evo = EvolutionEngine(force_offline=force_offline)
    nov = NoveltyEngine(force_offline=force_offline)
    board = CLevelBoard()
    vault = EvolutionVault()
    
    # 1. Propose Evolution
    focus_areas = ["Architecture", "Resilience", "Intelligence", "Security", "Self-Evolution"]
    area = focus_areas[loop_id % len(focus_areas)]
    print(f"[Phase 1] Proposing Evolution ({area})...")
    evolution = evo.propose_evolution(area)
    
    # 2. Mining for Novelty
    seed_traces = ["Leech Lattice", "Clifford Algebra", "Aletheia Resonance", "Autopoiesis", "Zero-Trust"]
    seed = seed_traces[loop_id % len(seed_traces)]
    print(f"[Phase 2] Mining for Novelty ({seed})...")
    novelty = nov.generate_novelty(seed)
    
    # 3. Board Review
    print("[Phase 3] Governance Review...")
    
    # Evolution Review
    evo_id = safe_get(evolution, "id")
    evo_title = safe_get(evolution, "title", "Evolution Proposal")
    evo_summary = safe_get(evolution, "summary", str(evolution))
    evo_risk = safe_get(evolution, "risk_score", 0.5)
    
    evo_review = board.review_proposal({
        "title": evo_title,
        "summary": evo_summary,
        "feasibility": True,
        "risks": [] if evo_risk < 0.5 else ["Potential resource overhead"],
        "market_eval": {"size": "N/A", "growth": "N/A"}
    })
    
    # Novelty Review
    nov_id = safe_get(novelty, "id")
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
    
    print(f"Evolution {evo_id}: {evo_review['decision']} (Score: {evo_review['aggregate_score']})")
    print(f"Novelty {nov_id}: {nov_review['decision']} (Score: {nov_review['aggregate_score']})")
    
    # 4. Success Application
    if evo_review['decision'] == "APPROVED" and evo_id:
        evo.apply_upgrade(evo_id)
        
    # 5. Log Sovereign Event
    event_data = {
        "loop_id": loop_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "evolution_id": evo_id,
        "novelty_id": nov_id,
        "evo_score": evo_review['aggregate_score'],
        "nov_score": nov_review['aggregate_score'],
        "offline_execution": force_offline
    }
    vault.log_item("sovereignty_events", event_data)
    
    return event_data

def main():
    parser = argparse.ArgumentParser(description="SRA Autonomy Loops")
    parser.add_argument("--loops", type=int, default=5, help="Number of evolution loops")
    parser.add_argument("--force-offline", action="store_true", help="Force agents into offline mode")
    args = parser.parse_args()
    
    print("="*60)
    print(f" SRA SOVEREIGN AUTONOMY HARDENING -- {args.loops} LOOPS")
    print("="*60)
    
    results = []
    for i in range(1, args.loops + 1):
        results.append(run_loop(i, force_offline=args.force_offline))
        time.sleep(1) # Breath between loops
        
    print("\n" + "="*60)
    print(f"  HARDENING COMPLETE: {len(results)} CYCLES LOGGED TO VAULT")
    print("="*60)

if __name__ == "__main__":
    main()
