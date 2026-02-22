
import unittest
from fastapi.testclient import TestClient
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.server.app import app

class TestPWARoutes(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_manifest_is_json(self):
        response = self.client.get("/manifest.json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/json")
        self.assertIn("Supreme Research Agent", response.json()["name"])

    def test_sw_is_js(self):
        response = self.client.get("/sw.js")
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/javascript", response.headers["content-type"])
        self.assertIn("CACHE_NAME", response.text)

if __name__ == "__main__":
    unittest.main()
