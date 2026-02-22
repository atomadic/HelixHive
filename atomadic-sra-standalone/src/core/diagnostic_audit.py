import sys
import os
import time
import json
import urllib.request
def manual_load_env():
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ[k] = v

manual_load_env()

import logging
from typing import Dict, List, Any

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ApexAudit")

class ApexAudit:
    """
    Apex Diagnostic Audit Engine v4.4.0.0
    Ensures absolute operational reliability and peak performance.
    """
    def __init__(self):
        self.results = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "status": "INITIATING",
            "checks": []
        }

    def run_full_audit(self):
        logger.info("[ApexAudit] Initiating Comprehensive System Probe...")
        
        # 1. API Key Audit
        self._audit_keys()
        
        # 2. Connectivity Audit
        self._audit_connectivity()
        
        # 3. Geometric Core Audit
        self._audit_geometric_core()
        
        # 4. Vault Integrity Audit
        self._audit_vault()

        # Final Status
        failed = [c for c in self.results["checks"] if c["status"] == "FAIL"]
        self.results["status"] = "HEALTHY" if not failed else "UNSTABLE"
        
        self.export_report()
        return self.results

    def _audit_keys(self):
        keys_to_check = [
            "SRA_API_KEY",
            "BING_SEARCH_V7_SUBSCRIPTION_KEY",
            "GOOGLE_SEARCH_API_KEY",
            "GOOGLE_SEARCH_CX",
            "GROQ_API_KEY",
            "GROQ_API_KEY_SECONDARY",
            "OPENROUTER_API_KEY",
            "OPENROUTER_API_KEY_SECONDARY"
        ]
        
        report = {"component": "API_KEYS", "status": "PASS", "details": {}}
        for key in keys_to_check:
            val = os.getenv(key)
            report["details"][key] = "ACTIVE" if val else "MISSING"
            if not val and key == "SRA_API_KEY": # Critical key
                report["status"] = "FAIL"
        
        self.results["checks"].append(report)

    def _audit_connectivity(self):
        targets = [
            {"name": "OLLAMA_LOCAL", "url": "http://localhost:11434", "critical": False},
            {"name": "SRA_IDE_LOCAL", "url": "http://localhost:8420", "critical": True},
            {"name": "HIVE_CENTRAL", "url": "https://api.atomadic.ai/hive/status", "critical": False}
        ]
        
        report = {"component": "CONNECTIVITY", "status": "PASS", "details": {}}
        for target in targets:
            try:
                with urllib.request.urlopen(target["url"], timeout=3) as res:
                    report["details"][target["name"]] = "ONLINE" if res.status == 200 else f"STATUS_{res.status}"
            except Exception as e:
                report["details"][target["name"]] = f"OFFLINE ({str(e)})"
                if target["critical"]:
                    report["status"] = "FAIL"
        
        self.results["checks"].append(report)

    def _audit_geometric_core(self):
        # Verify if E8 and Leech modules are loadable and responsive
        report = {"component": "GEOMETRIC_CORE", "status": "PASS", "details": {}}
        try:
            from src.core.e8_core import E8Core
            e8 = E8Core()
            report["details"]["E8"] = "READY"
        except Exception as e:
            report["details"]["E8"] = f"LOAD_FAILURE ({str(e)})"
            report["status"] = "FAIL"
            
        self.results["checks"].append(report)

    def _audit_vault(self):
        report = {"component": "EVOLUTION_VAULT", "status": "PASS", "details": {}}
        try:
            from src.core.evolution_vault import EvolutionVault
            vault = EvolutionVault()
            if vault.verify_integrity():
                report["details"]["Integrity"] = "VERIFIED"
            else:
                report["details"]["Integrity"] = "CHECKSUM_MISMATCH"
                report["status"] = "FAIL"
        except Exception as e:
            report["details"]["Vault"] = f"ACCESS_FAILURE ({str(e)})"
            report["status"] = "FAIL"
            
        self.results["checks"].append(report)

    def export_report(self):
        report_path = "data/last_audit_report.json"
        os.makedirs("data", exist_ok=True)
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"[ApexAudit] Audit Report exported to {report_path}")

if __name__ == "__main__":
    audit = ApexAudit()
    report = audit.run_full_audit()
    print(json.dumps(report, indent=2))
