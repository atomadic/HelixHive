
import sys
import os
import json

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.evolution_vault import EvolutionVault
from src.agents.opportunity_engine import OpportunityEngine
from src.agents.novelty_engine import NoveltyEngine
from src.agents.evolution_engine import EvolutionEngine

def seed_history(vault):
    """
    Seeds the vault with findings from the current session.
    """
    print("[Setup] Seeding historical data...")
    
    # Historical Opportunities
    opps = [
        {
            "id": "OA-FULL-AUTONOMY-001",
            "title": "Full Autonomous Tool Generation",
            "summary": "Connect JIT loop to live LLM backend.",
            "recommendation": "Implement immediately",
            "status": "APPROVED"
        },
        {
            "id": "OA-SWARM-LEARNING-001",
            "title": "Swarm Learning via Federated Tool Vaults",
            "summary": "Share generated tools between SRA instances.",
            "recommendation": "Research Feasibility",
            "status": "PENDING"
        },
        {
             "id": "OA-FULL-RECURSION-001",
             "title": "Recursive System Refactoring",
             "summary": "Optimization Agent crawls full src/ for upgrades.",
             "recommendation": "Pilot on src/tools",
             "status": "PENDING"
        }
    ]
    
    # Historical Novelties
    novs = [
        {
            "id": "NP-EVO-VAULT-001",
            "title": "Evolution Vault",
            "idea_summary": "Permanent storage for SRA learnings.",
            "type": "SRA Evolution"
        },
        {
            "id": "NP-SELF-OPTIM-001",
            "title": "Self-Optimization Engine",
            "idea_summary": "Agent optimization loop using profiler.",
            "type": "SRA Evolution"
        },
        {
            "id": "NP-HYPER-EVO-001",
            "title": "Meta-Optimization",
            "idea_summary": "Optimize the Optimizer.",
            "type": "SRA Evolution"
        }
    ]

    # Ingest
    for o in opps:
        # Check if exists (rudimentary check by ID implied, but log_item just appends for now)
        # We'll just append for this verify script, assuming fresh DB or duplicates ok for test
        vault.log_item("opportunities", o)
        
    for n in novs:
        vault.log_item("novelties", n)
        
    print(f"[Setup] Seeded {len(opps)} opportunities and {len(novs)} novelties.")

def test_governance():
    print("=== SRA Governance & Evolution Verification ===")
    
    vault = EvolutionVault()
    
    # 1. Seed History
    seed_history(vault)
    
    # 2. Test Engines (Generation)
    print("\n[Test] Running Engines...")
    
    opp_eng = OpportunityEngine()
    nov_eng = NoveltyEngine()
    evo_eng = EvolutionEngine()
    
    # Generate one of each (Mocking connection check logic inside engines is implicitly tested if they work)
    # Note: If Ollama is slow, this might take a moment.
    
    print("  -> Generating Opportunity...")
    o_item = opp_eng.generate_opportunity()
    if o_item: print(f"     [PASS] {o_item.get('title')}")
    else: print("     [FAIL] No Opportunity generated.")

    print("  -> Generating Novelty...")
    n_item = nov_eng.generate_novelty()
    if n_item: print(f"     [PASS] {n_item.get('title')}")
    else: print("     [FAIL] No Novelty generated.")

    print("  -> Generating Evolution...")
    e_item = evo_eng.propose_evolution()
    if e_item: print(f"     [PASS] {e_item.get('title')}")
    else: print("     [FAIL] No Evolution generated.")
    
    # 3. Verify Vault Persistence
    print("\n[Test] Verifying Vault Persistence...")
    all_data = vault.get_all()
    
    o_count = len(all_data["opportunities"])
    n_count = len(all_data["novelties"])
    e_count = len(all_data["evolutions"])
    
    print(f"  -> Vault contains: {o_count} Opps, {n_count} Novs, {e_count} Evos")
    
    if o_count >= 4 and n_count >= 4 and e_count >= 1: # 3 seeded + 1 generated
        print("[PASS] Vault counts look correct.")
    else:
        print("[FAIL] Vault counts lower than expected.")

if __name__ == "__main__":
    test_governance()
