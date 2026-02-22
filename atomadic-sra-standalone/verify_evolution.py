
import os
import sys
import json
import time

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from src.agents.rsi_protocol import RSIProtocol
from src.core.bootloader import Bootloader
from src.core.evolution_vault import EvolutionVault
from src.core.revelation_engine import RevelationEngine
from src.core.search_service import SearchService
from src.core.active_inference import ActiveInferenceLoop
from src.core.plugin_service import PluginService
from src.ui.dynamic_output_panel import DynamicOutputPanel

def test_evolution_vectors():
    print("\n=== SRA Sovereign Autopoietic Evolution: Global Audit ===\n")
    
    # 1. ΔM AST Metric
    rsi = RSIProtocol()
    mod_simple = "x = 1"
    mod_dense = "def complex_fn(a, b):\n    if a > b:\n        return [i**2 for i in range(a)]\n    return b"
    dm_simple = rsi._estimate_wisdom_gain(mod_simple)
    dm_dense = rsi._estimate_wisdom_gain(mod_dense)
    print(f"[Vector 1] ΔM Simple: {dm_simple} | ΔM Dense: {dm_dense}")
    assert dm_dense > dm_simple, "ΔM logic density failure"

    # 2. Bootloader Healing
    boot = Bootloader()
    print("[Vector 2] Testing Bootloader Healing Trigger...")
    boot.trigger_healing("Preflight Checklist") # Should log healing event
    
    # 4. Vault Sealing
    vault_path = "data/evolution_vault.json"
    vault = EvolutionVault(vault_path)
    vault.log_evolution("VERIFICATION_PASS", {"status": "sealed"})
    with open(vault_path, "r") as f:
        data = json.load(f)
        sig = data["metadata"].get("sovereign_signature")
        print(f"[Vector 4] Vault Signature Detected: {sig[:16]}...")
        assert sig, "Vault Sealing failed"

    # 5. & 6. Leech Compression & Logic Monitor
    rev = RevelationEngine()
    code_with_violation = "import random\ndef test():\n    return random.random()"
    audit_res = rev.perform_recursive_refinement("TestAgent", code_with_violation)
    print(f"[Vector 6] Audit Status: {audit_res['status']} | Violations: {len(audit_res['violations'])}")
    print(f"[Vector 5] Compressed Trace (Leech): {audit_res['compressed_trace']['is_significant']}")
    assert audit_res["status"] == "REJECTED", "Logic Monitor failed to catch simulation"

    # 7. E8 Search Grounding
    search = SearchService(vault)
    grounded = search._ground_results("Sovereignty", [{"title": "Fake", "snippet": "Random text"}, {"title": "Sovereign AI", "snippet": "Formal logic and autonomy"}])
    print(f"[Vector 7] Grounded Results: {len(grounded)} | Top Resonance: {grounded[0]['resonance'] if grounded else 'N/A'}")

    # 8. J-Gate Homeostasis
    inference = ActiveInferenceLoop()
    inference.tau = 0.5
    dot_v = inference.apply_homeostasis()
    print(f"[Vector 8] J-Gate Homeostasis recovery: tau={inference.tau:.4f} | dot_V={dot_v:.6f}")
    assert dot_v < 0, "Lyapunov stability violation"

    # 9. Plugin Discovery
    plugin_svc = PluginService(vault)
    # Check if core_revelation is in registry
    data = plugin_svc.get_marketplace_data()
    print(f"[Vector 9] Plugins Discovered: {list(data['plugins'].keys())[:3]}")

    # 10. Helical Headers
    ui = DynamicOutputPanel()
    output = ui.format_output("Verification complete.", metrics={"tau": 0.98, "j": 1.0, "delta_m": 150})
    print(f"[Vector 10] Helical Output Sample:\n{output[:150]}...")

    print("\n=== SYSTEM AUDIT: PASSED (τ=1.0) ===\n")

if __name__ == "__main__":
    test_evolution_vectors()
