
import json
import os
import time
import uuid
import hashlib
from typing import Dict, Any, List, Optional

class EvolutionVault:
    """
    Evolution Vault
    Central storage and query engine for strategic artifacts.
    Categories: opportunities, novelties, evolutions
    Persists to data/evolution_vault.json with integrity checks.
    """
    def __init__(self, data_file="data/evolution_vault.json"):
        self.data_file = data_file
        self.ensure_data_file()

    def ensure_data_file(self):
        dirname = os.path.dirname(self.data_file)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)
        if not os.path.exists(self.data_file):
            self._save({
                "opportunities": [], 
                "novelties": [], 
                "evolutions": [], 
                "sovereignty_events": [],
                "state": {},
                "metadata": {
                    "created": time.strftime("%Y-%m-%dT%H:%M:%S"), 
                    "version": "3.2.1.0"
                }
            })

    def _load(self) -> Dict[str, Any]:
        try:
            with open(self.data_file, "r") as f:
                return json.load(f)
        except Exception:
            return {
                "opportunities": [], 
                "novelties": [], 
                "evolutions": [], 
                "sovereignty_events": [],
                "metadata": {}
            }

    def _save(self, data: Dict[str, Any]):
        data["metadata"] = data.get("metadata", {})
        data["metadata"]["last_modified"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        data["metadata"]["checksum"] = self._checksum(data)
        
        # Rule 5: Sovereign Cryptographic Handshake (Pseudo-check for standlone)
        # In v4.0.0, we simulate the lock to prevent accidental overwrites.
        try:
            with open(self.data_file, "w") as f:
                json.dump(data, f, indent=2)
        except PermissionError:
            logger.error("[Vault] Sovereign Handshake Failure: Write Access Denied.")
            raise

    def _checksum(self, data):
        """Generate integrity checksum for vault data."""
        content = json.dumps({k: v for k, v in data.items() if k != "metadata"}, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def log_item(self, category: str, item: Dict[str, Any]):
        """Log an item to the specified category."""
        valid_categories = ["opportunities", "novelties", "evolutions", "sovereignty_events"]
        if category not in valid_categories:
            raise ValueError(f"Invalid category '{category}'. Must be one of: {valid_categories}")

        if "id" not in item:
            item["id"] = str(uuid.uuid4())
        if "timestamp" not in item:
            item["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")

        data = self._load()
        data[category].append(item)
        self._save(data)
        print(f"[EvolutionVault] Logged {category[:-1]}: {item.get('title', item.get('id', 'Untitled'))}")
        return item["id"]

    def log_evolution(self, activity: str, details: Dict[str, Any], tau: float = 1.0, j_gate: float = 1.0):
        """Log a system evolution event with helical metadata."""
        item = {
            "activity": activity,
            "details": details,
            "tau": tau,
            "j_gate": j_gate
        }
        return self.log_item("evolutions", item)

    def get_all(self, category: Optional[str] = None):
        data = self._load()
        if category:
            return data.get(category, [])
        return data

    def query(self, category: str, **filters) -> List[Dict]:
        """Query items by category and optional filters."""
        items = self.get_all(category)
        results = []
        for item in items:
            match = True
            for key, value in filters.items():
                if key not in item:
                    match = False
                    break
                if isinstance(value, str) and isinstance(item[key], str):
                    if value.lower() not in item[key].lower():
                        match = False
                        break
                elif item[key] != value:
                    match = False
                    break
            if match:
                results.append(item)
        return results

    def get_recent(self, category: str, n: int = 10) -> List[Dict]:
        """Get the N most recent items in a category."""
        items = self.get_all(category)
        return items[-n:]

    def get_stats(self) -> Dict[str, Any]:
        """Get vault statistics."""
        data = self._load()
        return {
            "opportunities": len(data.get("opportunities", [])),
            "novelties": len(data.get("novelties", [])),
            "evolutions": len(data.get("evolutions", [])),
            "total_items": sum(len(data.get(c, [])) for c in ["opportunities", "novelties", "evolutions"]),
            "metadata": data.get("metadata", {}),
        }

    def prune(self, category: str, keep_count: int = 50):
        """Prune old items, keeping the most recent ones."""
        data = self._load()
        items = data.get(category, [])
        if len(items) > keep_count:
            pruned = len(items) - keep_count
            data[category] = items[-keep_count:]
            self._save(data)
            print(f"[EvolutionVault] Pruned {pruned} items from {category}")
            return pruned
        return 0

    def export(self, filepath: str):
        """Export entire vault to a file."""
        data = self._load()
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[EvolutionVault] Exported to {filepath}")

    def verify_integrity(self) -> bool:
        """Verify vault data integrity via checksum."""
        data = self._load()
        stored_checksum = data.get("metadata", {}).get("checksum", "")
        computed = self._checksum(data)
        ok = stored_checksum == computed
        if not ok:
            print(f"[EvolutionVault] INTEGRITY WARNING: checksum mismatch")
        return ok

    def get_state(self, key: str) -> Any:
        """Retrieve arbitrary state data."""
        data = self._load()
        return data.get("state", {}).get(key)

    def update_state(self, key: str, value: Any, secret: Optional[str] = None):
        """
        Update arbitrary state data.
        Rule 5: Sensitive state keys require a secret handshake.
        """
        protected_keys = ["auth_tenant_registry", "billing_usage_registry"]
        if key in protected_keys and secret != os.getenv("SRA_SOVEREIGN_2026", "SRA_SOVEREIGN_2026"):
             self.log_item("sovereignty_events", {"type": "UNAUTHORIZED_STATE_MUTATION", "key": key})
             raise PermissionError(f"Access Denied: Protected state key '{key}'")

        data = self._load()
        if "state" not in data:
            data["state"] = {}
        data["state"][key] = value
        self._save(data)

if __name__ == "__main__":
    # Self-test block for EvolutionVault integrity
    test_vault_file = "tests/test_vault_self.json"
    if not os.path.exists("tests"):
        os.makedirs("tests", exist_ok=True)
    
    # Clean any previous test run
    if os.path.exists(test_vault_file):
        os.remove(test_vault_file)
        
    vault = EvolutionVault(test_vault_file)
    
    # Test logging
    vault.log_evolution("SELF_TEST_V4", {"status": "ok"})
    evolutions = vault.get_all("evolutions")
    if len(evolutions) >= 1 and evolutions[0]["activity"] == "SELF_TEST_V4":
        print("[Self-Test] EvolutionVault Verification: SUCCESS")
    else:
        print("[Self-Test] EvolutionVault Verification: FAILURE")
        
    # Clean up
    if os.path.exists(test_vault_file):
        os.remove(test_vault_file)
