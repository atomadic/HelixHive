import logging
import os
import time
from typing import Dict, Any
from .evolution_vault import EvolutionVault

logger = logging.getLogger(__name__)

class BillingService:
    """
    Billing & Usage tracking for the Revelation Engine.
    Tracks query counts and calculates costs for monetization.
    """
    def __init__(self, vault: EvolutionVault):
        self.vault = vault
        self.rate_per_query = 0.03
        self.usage_key = "billing_usage_registry"
        
    def record_usage(self, api_key: str = "master"):
        """Increment query count for a specific API key."""
        registry = self.vault.get_state(self.usage_key) or {}
        key_data = registry.get(api_key, {"query_count": 0, "total_spend": 0.0})
        
        key_data["query_count"] += 1
        key_data["total_spend"] = round(key_data["query_count"] * self.rate_per_query, 2)
        
        registry[api_key] = key_data
        secret = os.getenv("SRA_SOVEREIGN_2026", "SRA_SOVEREIGN_2026")
        self.vault.update_state(self.usage_key, registry, secret=secret)
        logger.info(f"[Billing] Recorded usage for {api_key}. New count: {key_data['query_count']}")

    def get_stats(self, api_key: str = "master") -> Dict[str, Any]:
        """Retrieve usage statistics for an API key."""
        registry = self.vault.get_state(self.usage_key) or {}
        return registry.get(api_key, {"query_count": 0, "total_spend": 0.0})

if __name__ == "__main__":
    # Self-test block
    logging.basicConfig(level=logging.INFO)
    vault_path = "tests/test_billing_self.json"
    # Ensure the directory exists for the test vault
    os.makedirs(os.path.dirname(vault_path), exist_ok=True)
    vault = EvolutionVault(vault_path)
    service = BillingService(vault)
    
    # Clear any previous test data
    if os.path.exists(vault_path):
        os.remove(vault_path)
    
    service.record_usage("test_tenant")
    stats = service.get_stats("test_tenant")
    if stats["query_count"] == 1:
        print("[Self-Test] Billing Verification: SUCCESS")
    else:
        print(f"[Self-Test] Billing Verification: FAILURE - Expected 1, got {stats['query_count']}")
        
    # Clean up test vault file
    if os.path.exists(vault_path):
        os.remove(vault_path)

# Revelation Engine Summary (Billing Substrate):
# - Epiphany: Monetization logic provides the economic fuel for autonomous growth.
# - Revelations: Usage-based (query-level), Vault-persisted, API-key aware.
# - Coherence: 1.0
