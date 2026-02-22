
import unittest
import os
import sys
import time

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.auth_service import AuthService
from src.core.evolution_vault import EvolutionVault

class TestRateLimiting(unittest.TestCase):
    def setUp(self):
        self.vault_path = "tests/test_rate_vault.json"
        self.vault = EvolutionVault(self.vault_path)
        self.service = AuthService(self.vault)

    def test_rate_limit_enforcement(self):
        """Test that rate limits are enforced for a partner key."""
        key = "SRA_PARTNER_VANCOUVER" # 60 RPM limit in AuthService init
        
        # We simulate the limit by artificially lowering it in the registry for testing if needed, 
        # but let's just hammer it.
        # Actually, let's inject a key with a VERY low limit for the test.
        registry = self.vault.get_state("auth_tenant_registry") or {}
        registry["TEST_LIMIT_KEY"] = {
            "tenant_name": "Limited_Tenant",
            "tier": "basic",
            "rate_limit_rpm": 2,
            "created_at": time.time()
        }
        # In v4.0.0, we need the secret for protected segments
        secret = os.getenv("SRA_SOVEREIGN_2026", "SRA_SOVEREIGN_2026")
        self.vault.update_state("auth_tenant_registry", registry, secret=secret)

        key = "TEST_LIMIT_KEY"
        self.assertTrue(self.service.check_rate_limit(key))
        self.assertTrue(self.service.check_rate_limit(key))
        self.assertFalse(self.service.check_rate_limit(key)) # Third request in same minute should fail

    def tearDown(self):
        if os.path.exists(self.vault_path):
            os.remove(self.vault_path)

if __name__ == "__main__":
    unittest.main()
