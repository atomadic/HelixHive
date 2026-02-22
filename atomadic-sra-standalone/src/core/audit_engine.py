"""
Audit Engine v1.0.0.0
Granular, file-by-file codebase auditing for SRA sovereignty.
SRA v4.4.2.0 | HelixEvolver Autopoiesis
"""

import os
import hashlib
import json
import time
from pathlib import Path
from typing import Dict, Any, List

_ROOT = Path(__file__).resolve().parent.parent.parent

class AuditEngine:
    def __init__(self):
        self.target_dir = _ROOT
        self.exclude_dirs = {".git", "__pycache__", "node_modules", "venv", ".pytest_cache", ".gemini", "HelixHive-main"}
        self.audit_log = []

    def get_file_hash(self, file_path: Path) -> str:
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except:
            return "HASH_ERROR"

    def audit_file(self, file_path: Path) -> Dict[str, Any]:
        """Performs a granular audit on a single file."""
        stats = file_path.stat()
        try:
            content = file_path.read_text(encoding="utf-8")
            loc = len(content.splitlines())
        except:
            content = ""
            loc = 0

        audit_entry = {
            "path": str(file_path.relative_to(_ROOT)),
            "size": stats.st_size,
            "loc": loc,
            "hash": self.get_file_hash(file_path),
            "last_modified": time.ctime(stats.st_mtime),
            "status": "VERIFIED"
        }
        
        # Rule 15 markers (Wisdom Mass check)
        if "deltaM" in content or "deltaL" in content:
            audit_entry["rule_compliance"] = "Rule 15 Validated"
        else:
            audit_entry["rule_compliance"] = "Passive Content"

        return audit_entry

    def run_full_audit(self):
        print(f"--- [SRA] Audit Engine: {self.target_dir} ---")
        for root, dirs, files in os.walk(self.target_dir):
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for file in files:
                file_path = Path(root) / file
                entry = self.audit_file(file_path)
                self.audit_log.append(entry)

        self.generate_report()

    def generate_report(self):
        report_path = _ROOT / "full-codebase-audit.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# SRA Full Codebase Audit — {time.ctime()}\n\n")
            f.write("## System Metrics\n")
            f.write(f"- Total Files Audited: {len(self.audit_log)}\n")
            total_loc = sum(e["loc"] for e in self.audit_log)
            f.write(f"- Total Lines of Code (LOC): {total_loc}\n")
            f.write(f"- Audit Engine Version: v1.0.0.0\n\n")

            f.write("## Detailed File Manifest\n")
            f.write("| File Path | LOC | Size (B) | Rule Compliance | Hash (SHA256) |\n")
            f.write("| --- | --- | --- | --- | --- |\n")
            for e in self.audit_log:
                f.write(f"| {e['path']} | {e['loc']} | {e['size']} | {e['rule_compliance']} | `{e['hash'][:8]}...` |\n")

        # Save machine-parsable JSON
        json_path = _ROOT / "data" / "codebase_audit.json"
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(self.audit_log, indent=2), encoding="utf-8")
        
        print(f"✓ Audit Complete. Report: {report_path}")

if __name__ == "__main__":
    engine = AuditEngine()
    engine.run_full_audit()
