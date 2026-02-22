"""
Autonomous Error Repair v1.0.0.0
Self-healing logic for the SRA substrate.
SRA v4.4.2.0 | HelixEvolver Autopoiesis
"""

import os
import json
import logging
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
logger = logging.getLogger("ErrorRepair")

class ErrorRepair:
    def __init__(self):
        self.repair_log = _ROOT / "data" / "repair_history.jsonl"

    def log_repair(self, target: str, action: str, result: str):
        event = {"target": target, "action": action, "result": result}
        with open(self.repair_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

    def repair_missing_dir(self, dir_path: str):
        p = _ROOT / dir_path
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            self.log_repair(dir_path, "CREATE_DIR", "SUCCESS")
            return True
        return False

    def repair_env_file(self):
        env_path = _ROOT / ".env"
        if not env_path.exists():
            example = _ROOT / ".env.example"
            if example.exists():
                import shutil
                shutil.copy(example, env_path)
                self.log_repair(".env", "RESTORE_FROM_EXAMPLE", "SUCCESS")
                return True
            else:
                # Create default .env
                content = "SRA_API_KEY=SRA_SOVEREIGN_2026\nOLLAMA_BASE_URL=http://localhost:11434\n"
                env_path.write_text(content, encoding="utf-8")
                self.log_repair(".env", "CREATE_DEFAULT", "SUCCESS")
                return True
        return False

    def run_healing_cycle(self, check_results: list):
        """Processes bootloader diagnostics and attempts fixes."""
        print("[*] Initiating Autonomous Healing Cycle...")
        healed = 0
        for check in check_results:
            if not check["success"]:
                msg = check["message"]
                if ".env file missing" in msg:
                    if self.repair_env_file(): healed += 1
                elif "directory missing" in msg:
                    # Logic to parse dir from msg if added to bootloader
                    pass
        
        print(f"✓ Healing Cycle Finished. Issues resolved: {healed}")
        return healed > 0

if __name__ == "__main__":
    repair = ErrorRepair()
    repair.repair_missing_dir("data")
    repair.repair_env_file()
