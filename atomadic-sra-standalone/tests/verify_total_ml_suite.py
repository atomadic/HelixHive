
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def verify_ml_expansion():
    print("=== SRA Total ML Expansion Verification (Phase 6) ===")
    
    from src.core.ml_hub import MLHub
    from src.agents.luminary_base import LuminaryBase
    from src.agents.goal_engine import GoalEngine
    from src.agents.toolsmith_agent import ToolsmithAgent
    from src.agents.leech_outer import LeechOuter
    from src.agents.formal_precision import FormalPrecision
    from src.core.entropy_core import EntropyCore
    from src.core.e8_core import E8Core
    from src.core.revelation_engine import RevelationEngine
    from src.governance.c_level_board import CLevelBoard
    from src.governance.debate_engine import DebateEngine
    from src.core.ollama_service import OllamaService
    
    hub = MLHub()
    
    # Register and Test Modules
    print("\n[Audit] Registering modules to MLHub...")
    hub.register_module("AIH", LuminaryBase("AIH-Tester"))
    hub.register_module("GDGA", GoalEngine())
    hub.register_module("NTS", ToolsmithAgent())
    hub.register_module("LMC", LeechOuter())
    hub.register_module("Prove", FormalPrecision())
    hub.register_module("Entropy", EntropyCore())
    hub.register_module("E8", E8Core())
    hub.register_module("RSR", RevelationEngine())
    hub.register_module("DAS", CLevelBoard())
    hub.register_module("Debate", DebateEngine())
    
    # 1. Test AIH (NOV-004)
    print("\n[Test 1] AIH: Active Inference Homeostasis")
    res = hub.invoke_module("AIH", "apply_aih", 0.8) # Surprise
    if res is None: # Success usually means no return or state update
        print("  [PASS] AIH invoked successfully.")

    # 2. Test GDGA (NOV-005)
    print("\n[Test 2] GDGA: Gradient Goal Alignment")
    goal_engine = hub.modules["GDGA"]
    goal_engine.add_goal("Transcend Intelligence")
    res = hub.invoke_module("GDGA", "apply_gdga", "G-0000", 0.9) # High reward
    if res and res["priority"] > 1.0:
        print(f"  [PASS] GDGA refined priority: {res['priority']:.4f}")

    # 3. Test LMC (NOV-007)
    print("\n[Test 3] LMC: Latent Memory Compaction")
    leech = hub.modules["LMC"]
    leech.capture_trace("Arxiv", "Deep research on autopoietic agents...")
    res = hub.invoke_module("LMC", "apply_lmc")
    if res["status"] == "SUCCESS":
        print(f"  [PASS] LMC generated lattice: {res['lattice_id']}")

    # 4. Test RSR (NOV-015)
    print("\n[Test 4] RSR: Recursive Sovereign Refinement")
    res = hub.invoke_module("RSR", "perform_recursive_refinement", "Toolsmith", "def execute(): simulate()")
    if "Rule III" in str(res["violations"]):
        print("  [PASS] RSR detected Axiom violation successfully.")

    hub.perform_system_sync()
    print("\n=== Phase 6 Verification Complete ===")

if __name__ == "__main__":
    verify_ml_expansion()
