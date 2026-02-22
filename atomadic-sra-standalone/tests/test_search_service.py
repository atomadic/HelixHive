
import asyncio
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.search_service import SearchService
from src.core.evolution_vault import EvolutionVault

class TestSearchService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.vault = MagicMock(spec=EvolutionVault)
        # Mock vault query to return empty (no cache)
        self.vault.query.return_value = []
        self.service = SearchService(self.vault)

    async def test_simulated_search(self):
        """Test that search falls back to simulation when no keys are provided."""
        query = "latest news on SRA"
        results = await self.service.search(query, count=2)
        
        self.assertEqual(len(results), 2)
        self.assertIn("synthetic", results[0]["snippet"].lower())
        
        # Verify cache was saved
        self.vault.log_evolution.assert_called_once()

    async def test_cache_hit(self):
        """Test that search returns cached results if available and not expired."""
        query = "cached query"
        self.vault.query.return_value = [{
            "timestamp_unix": 10**10, # Way in the future
            "details": {"results": [{"title": "Cached Result", "url": "...", "snippet": "..."}]}
        }]
        
        results = await self.service.search(query)
        self.assertEqual(results[0]["title"], "Cached Result")
        # Ensure log_evolution was NOT called (no new search performed)
        self.vault.log_evolution.assert_not_called()

if __name__ == "__main__":
    unittest.main()
