
import logging
import time
import os
from typing import Dict, Any, Optional
from .evolution_vault import EvolutionVault

logger = logging.getLogger(__name__)

class AuthService:
    """
    Sovereign Multi-Tenant Authentication Service.
    Manages API key lifecycle, rate limits, and tenant metadata.
    """
    def __init__(self, vault: EvolutionVault):
        self.vault = vault
        self.auth_key = "auth_tenant_registry"
        self._ensure_master_key()

    def _ensure_master_key(self):
        """Ensures the master sovereign key exists in the registry."""
        registry = self.vault.get_state(self.auth_key) or {}
        master_key = "SRA_SOVEREIGN_2026" # Default from app.py
        
        if master_key not in registry:
            registry[master_key] = {
                "tenant_name": "Atomadic_Internal",
                "tier": "sovereign",
                "rate_limit_rpm": 999999,
                "created_at": time.time()
            }
            # Add a demo partner key
            registry["SRA_PARTNER_VANCOUVER"] = {
                "tenant_name": "Cascadia_Research_Hub",
                "tier": "pro",
                "rate_limit_rpm": 60,
                "created_at": time.time()
            }
            secret = os.getenv("SRA_SOVEREIGN_2026", "SRA_SOVEREIGN_2026")
            self.vault.update_state(self.auth_key, registry, secret=secret)
            logger.info("[Auth] Initialized Tenant Registry with Sovereign and Partner keys.")

    def verify_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Verify API key and return tenant metadata."""
        registry = self.vault.get_state(self.auth_key) or {}
        return registry.get(api_key)

    def check_rate_limit(self, api_key: str) -> bool:
        """
        Check if the tenant has exceeded their rate limit.
        Simple implementation: tracks last 60s in the vault.
        """
        # Note: In high-production, use Redis. For SRA Standalone, Vault state is sufficient.
        current_time = int(time.time())
        limit_key = f"rate_limit_{api_key}_{current_time // 60}"
        
        tenant = self.verify_key(api_key)
        if not tenant:
            return False
            
        count = self.vault.get_state(limit_key) or 0
        if count >= tenant["rate_limit_rpm"]:
            logger.warning(f"[Auth] Rate limit exceeded for {tenant['tenant_name']}")
            return False
            
        self.vault.update_state(limit_key, count + 1)
        return True

if __name__ == "__main__":
    # Self-test block for v4.1.0.0 verification
    logging.basicConfig(level=logging.INFO)
    vault_path = "tests/test_auth_self.json"
    vault = EvolutionVault(vault_path)
    service = AuthService(vault)
    
    test_key = "SRA_SOVEREIGN_2026"
    print(f"[Self-Test] Verifying Key: {test_key}")
    tenant = service.verify_key(test_key)
    if tenant and tenant["tenant_name"] == "Atomadic_Internal":
        print("[Self-Test] Verification Status: SUCCESS")
    else:
        print("[Self-Test] Verification Status: FAILURE")
        
    if os.path.exists(vault_path):
        os.remove(vault_path)
