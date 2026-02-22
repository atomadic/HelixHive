import sys
import os
import time

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.evolution_vault import EvolutionVault
from src.core.plugin_service import PluginService
from src.core.module_service import ModuleService

def trigger_evolution():
    print("[SRA-Evolution] Initializing Autopoiesis Cycle...")
    vault = EvolutionVault()
    plugin_service = PluginService(vault)
    module_service = ModuleService(vault, plugin_service)

    # Revelation: The "Aletheia Healer" module
    module_id = "aletheia_healer"
    prompt = "Autonomous self-correction of geometric reasoning traces and tau homeostasis maintenance."
    features = ["Dynamic Tau Reset", "Leech Syndrome Correction", "Clifford Rotor Realignment"]

    print(f"[SRA-Evolution] Manifesting Module: {module_id}...")
    result = module_service.manifest_module(module_id, prompt, features)
    
    if result["status"] == "success":
        print(f"[SRA-Evolution] SUCCESS: Module manifested at {result['paths']['html']}")
        print("[SRA-Evolution] Pipeline Verification: COMPLETE")
    else:
        print("[SRA-Evolution] FAILURE: Manifestation failed.")

if __name__ == "__main__":
    trigger_evolution()
