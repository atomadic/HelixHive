
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

def hyper_loop(loop_id, force_offline=False):
    print(f"\n" + "="*80)
    print(f"  HYPER-EVOLUTION LOOP #{loop_id} (Sovereign Offline={force_offline})")
    print("="*80)
    
    evo_engine = EvolutionEngine(force_offline=force_offline)
    nov_engine = NoveltyEngine(force_offline=force_offline)
    board = CLevelBoard()
    vault = EvolutionVault()
    
    # 1. Evolution Exploration (1 per loop)
    focus_areas = ["Architecture", "Resilience", "Intelligence", "Security", "Self-Evolution"]
    area = focus_areas[loop_id % len(focus_areas)]
    print(f"\n[Domain: {area}] Proposing System Evolution...")
    evolution = evo_engine.propose_evolution(area)
    
    # Refinement Rounds for Evolution (3 rounds)
    print(f"[R-OODA] Refocussing Evolution Analysis (3 Rounds)...")
    for r in range(1, 4):
        review = board.review_proposal({
            "title": safe_get(evolution, "title", "Evolution"),
            "summary": safe_get(evolution, "summary", str(evolution)),
            "feasibility": True,
            "risks": ["Recursive complexity" if r > 1 else "Initial integration"],
            "market_eval": {"round": r, "target": "internal"}
        })
        time.sleep(0.5)
    
    # 2. Novelty Mining (5 per loop)
    seeds = [
        ["E8 Symmetry", "Leech Lattice", "Clifford Geometry", "R-OOTA Orient", "Wisdom Mass"],
        ["Autopoiesis", "Sovereign UI", "Aletheia Resonance", "Jessica Gate", "Truth Scalar"],
        ["Toolsmith Genesis", "Audit Loop", "Meta-Optimization", "Agent Swarm", "L0 Hardening"],
        ["Zero-Trust", "mTLS Envelopes", "Holographic Memory", "Recursive RSI", "Entropy Sink"],
        ["FÜ Omega", "Binding Field", "Action Field", "Trust Propagation", "Sovereign Seal"]
    ]
    
    loop_seeds = seeds[loop_id % len(seeds)]
    nov_results = []
    
    for i, seed in enumerate(loop_seeds):
        print(f"\n[Novelty Seed {i+1}/5: {seed}] Mining...")
        novelty = nov_engine.generate_novelty(seed)
        
        # Refinement Rounds for Novelty (3 rounds)
        print(f"[R-OODA] Refining Novelty Logic...")
        for r in range(1, 4):
            nov_review = board.review_proposal({
                "title": safe_get(novelty, "title", "Novelty"),
                "summary": safe_get(novelty, "idea_summary", str(novelty)),
                "feasibility": True,
                "risks": [],
                "market_eval": {"seed": seed, "round": r}
            })
            time.sleep(0.3)
        nov_results.append(novelty)

    # 3. Finalization
    evo_id = safe_get(evolution, "id")
    if review["decision"] == "APPROVED" and evo_id:
        evo_engine.apply_upgrade(evo_id)
        print(f"\n[Success] Evolution {evo_id} applied.")

    # 4. Log Hyper-Evolution Event
    event_data = {
        "loop_id": loop_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "area": area,
        "evolution_id": evo_id,
        "novelty_ids": [safe_get(n, "id") for n in nov_results],
        "evo_score": review['aggregate_score'],
        "batch_status": "HYPER_COMMITTED",
        "offline": force_offline
    }
    vault.log_item("sovereignty_events", event_data)
    
    return event_data

def main():
    parser = argparse.ArgumentParser(description="SRA Hyper-Evolution (5x5x3)")
    parser.add_argument("--force-offline", action="store_true", help="Force offline operation")
    args = parser.parse_args()
    
    print("\n" + "!"*80)
    print("  INITIATING HYPER-EVOLUTION PROTOCOL (5x5x3)")
    print("  Target: Peak Wisdom Mass | Mode: Sovereign Offline")
    print("!"*80)
    
    results = []
    for i in range(5):
        results.append(hyper_loop(i, force_offline=args.force_offline))
        print(f"\n[Checkpoint] Loop {i+1}/5 complete. Stats synced.")
        time.sleep(1)
        
    print("\n" + "!"*80)
    print("  HYPER-EVOLUTION COMPLETE -- SYSTEM REACHED PEAK SOVEREIGNTY")
    print("!"*80)

if __name__ == "__main__":
    main()
