
import unittest
import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.auth_service import AuthService
from src.core.evolution_vault import EvolutionVault

class TestMultiTenantAuth(unittest.TestCase):
    def setUp(self):
        self.vault_path = "tests/test_auth_vault.json"
        self.vault = EvolutionVault(self.vault_path)
        self.service = AuthService(self.vault)

    def test_verify_master_key(self):
        """Test master sovereign key verification."""
        tenant = self.service.verify_key("SRA_SOVEREIGN_2026")
        self.assertIsNotNone(tenant)
        self.assertEqual(tenant["tenant_name"], "Atomadic_Internal")
        self.assertEqual(tenant["tier"], "sovereign")

    def test_verify_partner_key(self):
        """Test partner key verification."""
        tenant = self.service.verify_key("SRA_PARTNER_VANCOUVER")
        self.assertIsNotNone(tenant)
        self.assertEqual(tenant["tenant_name"], "Cascadia_Research_Hub")
        self.assertEqual(tenant["tier"], "pro")

    def test_verify_invalid_key(self):
        """Test rejection of invalid keys."""
        tenant = self.service.verify_key("INVALID_EXTRACTOR_KEY")
        self.assertIsNone(tenant)

    def tearDown(self):
        if os.path.exists(self.vault_path):
            os.remove(self.vault_path)

if __name__ == "__main__":
    unittest.main()
