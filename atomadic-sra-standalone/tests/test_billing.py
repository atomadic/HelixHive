
import unittest
import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.billing_service import BillingService
from src.core.evolution_vault import EvolutionVault

class TestBillingService(unittest.TestCase):
    def setUp(self):
        self.vault_path = "tests/test_billing_vault.json"
        self.vault = EvolutionVault(self.vault_path)
        self.service = BillingService(self.vault)

    def test_record_usage(self):
        """Test incrementing usage count."""
        key = "test_agent"
        self.service.record_usage(key)
        stats = self.service.get_stats(key)
        self.assertEqual(stats["query_count"], 1)
        self.assertEqual(stats["total_spend"], 0.03)
        
        self.service.record_usage(key)
        stats = self.service.get_stats(key)
        self.assertEqual(stats["query_count"], 2)
        self.assertEqual(stats["total_spend"], 0.06)

    def tearDown(self):
        # Cleanup
        if os.path.exists(self.vault_path):
            os.remove(self.vault_path)

if __name__ == "__main__":
    unittest.main()
