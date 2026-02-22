
import unittest
import sys
import os
import threading
import time
import uvicorn

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.sdk.sra_client import SRAClient
from src.server.app import app

class TestSDKConnectivity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start the server in a background thread
        cls.server_thread = threading.Thread(
            target=uvicorn.run, 
            args=(app,), 
            kwargs={"host": "127.0.0.1", "port": 8005, "log_level": "info"},
            daemon=True
        )
        cls.server_thread.start()
        time.sleep(2) # Wait for server to boot
        cls.client = SRAClient(base_url="http://127.0.0.1:8005", api_key="SRA_SOVEREIGN_2026")

    def test_research_success(self):
        """Test successful revelation via SDK."""
        result = self.client.research("Vancouver Tech Expo 2026")
        self.assertIn("epiphanies", result)
        self.assertIn("coherence", result)
        self.assertGreaterEqual(result["coherence"], 0.8)

    def test_auth_failure(self):
        """Test that invalid API key triggers 401."""
        bad_client = SRAClient(base_url="http://127.0.0.1:8005", api_key="BAD_KEY")
        with self.assertRaises(RuntimeError) as cm:
            bad_client.research("Unauthorized query")
        self.assertIn("401", str(cm.exception))

if __name__ == "__main__":
    unittest.main()
