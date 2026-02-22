
import unittest
import os
import sys
import shutil

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.app_generator import AppGenerator

class TestAppGenerator(unittest.TestCase):
    def setUp(self):
        self.static_dir = "tests/test_static"
        self.generator = AppGenerator(self.static_dir)

    def test_manifest_pwa(self):
        """Test generating a functional PWA bundle."""
        app_id = "vancouver_runner_app"
        prompt = "Create a fitness app for Vancouver"
        features = ["GPS Tracking", "Rain-safe UI"]
        
        result = self.generator.manifest_pwa(app_id, prompt, features)
        
        self.assertEqual(result["app_id"], app_id)
        self.assertIn("/static/apps/vancouver_runner_app/index.html", result["url"])
        
        # Verify filesystem
        app_dir = os.path.join(self.static_dir, "apps", app_id)
        self.assertTrue(os.path.exists(os.path.join(app_dir, "index.html")))
        self.assertTrue(os.path.exists(os.path.join(app_dir, "manifest.json")))
        
        with open(os.path.join(app_dir, "index.html"), "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("GPS Tracking", content)
            self.assertIn("v4.0.0.0", content)

    def tearDown(self):
        if os.path.exists(self.static_dir):
            shutil.rmtree(self.static_dir)

if __name__ == "__main__":
    unittest.main()
