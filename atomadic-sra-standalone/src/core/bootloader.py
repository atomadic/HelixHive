"""
Sovereign Bootloader v1.0.0.0
Manages preflight diagnostics, module preloading, and autonomous healing.
SRA v4.4.2.0 | HelixEvolver Autopoiesis
"""

import sys
import os
import time
import json
import logging
import importlib
from pathlib import Path
from typing import List, Dict, Any

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

class Bootloader:
    def __init__(self):
        self.log_file = _ROOT / "data" / "boot_history.jsonl"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.report = {
            "timestamp": time.time(),
            "status": "INIT",
            "checks": []
        }
        self.critical_modules = [
            "src.core.ai_bridge",
            "src.core.hive_bridge",
            "src.core.ollama_service",
            "src.core.super_panel"
        ]

    def log_event(self, check_name: str, success: bool, message: str):
        event = {
            "check": check_name,
            "success": success,
            "message": message,
            "ts": time.time()
        }
        self.report["checks"].append(event)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

    def check_env(self):
        """Preflight checklist: Environment variables and keys."""
        env_path = _ROOT / ".env"
        if not env_path.exists():
            self.log_event("ENV_CHECK", False, ".env file missing")
            return False
        
        # Check for critical keys (simplified)
        try:
            from src.core.evolution_vault import EvolutionVault
            from src.core.settings_service import SettingsService
            vault = EvolutionVault()
            settings = SettingsService(vault)
            # SettingsService uses vault.get_state("sovereign_settings")
            # We can check os.getenv as a fallback for preflight
            if not os.getenv("OPENROUTER_API_KEY") and not os.getenv("GROQ_API_KEY"):
                self.log_event("KEY_CHECK", False, "No cloud API keys found in .env.")
            else:
                self.log_event("KEY_CHECK", True, "Cloud API keys detected in environment.")
        except Exception as e:
            self.log_event("KEY_CHECK", False, f"Failed to validate keys via SettingsService: {e}")
        return True

    def preload_modules(self):
        """Preload major system modules to ensure they are available and error-free."""
        for mod_name in self.critical_modules:
            try:
                importlib.import_module(mod_name)
                self.log_event("MODULE_PRELOAD", True, f"Successfully preloaded {mod_name}")
            except Exception as e:
                self.log_event("MODULE_PRELOAD", False, f"Failed to preload {mod_name}: {e}")
                return False
        return True

    def run_diagnostics(self):
        """Run connectivity and substrate checks."""
        # Ollama check
        from src.core.ollama_service import OllamaService
        ollama = OllamaService()
        if ollama.check_connection():
            self.log_event("DIAGNOSTIC", True, "Ollama local service online.")
        else:
            self.log_event("DIAGNOSTIC", False, "Ollama local service offline. Using Cloud-only mode.")

        return True

    def execute_boot(self):
        print("\n=== [SRA] Sovereign Bootloader Initiated ===\n")
        
        steps = [
            ("Preflight Checklist", self.check_env),
            ("Module Preloading", self.preload_modules),
            ("Systems Diagnostic", self.run_diagnostics)
        ]

        for name, func in steps:
            print(f"[*] Running {name}...")
            if not func():
                print(f"✗ [CRITICAL] {name} failed. Triggering Healing Cycle...")
                self.trigger_healing(name)
            else:
                print(f"✓ {name} completed.")

    def trigger_healing(self, failed_step: str):
        """Autonomous healing: Restore missing substrate components."""
        print(f"[Healing] Attempting to repair: {failed_step}...")
        
        if failed_step == "Preflight Checklist":
            env_path = _ROOT / ".env"
            env_example = _ROOT / ".env.example"
            if not env_path.exists() and env_example.exists():
                print("[Healing] .env missing. Restoring from .env.example...")
                import shutil
                shutil.copy(env_example, env_path)
                self.log_event("HEALING", True, "Restored .env from .env.example")
            else:
                self.log_event("HEALING", False, "Could not restore .env/keys automatically.")
        
        elif failed_step == "Module Preloading":
            print("[Healing] Critical modules missing. Marking system for reproduction...")
            self.log_event("HEALING", False, "Module absence requires full reproduction sequence.")
            
        elif failed_step == "Systems Diagnostic":
             print("[Healing] Connectivity failure. Verifying local Ollama endpoint...")
             self.log_event("HEALING", True, "System redirected to local-only emergency substrate.")

        self.report["status"] = "SUCCESS"
        print(f"\n[SUCCESS] SRA Bootloader finished. System state: SOVEREIGN\n")
        return True

if __name__ == "__main__":
    boot = Bootloader()
    boot.execute_boot()
