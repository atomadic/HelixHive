
import unittest
import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.branding_service import BrandingService

class TestBrandingService(unittest.TestCase):
    def setUp(self):
        self.service = BrandingService()

    def test_default_theme(self):
        """Test default branding tokens."""
        config = self.service.get_config("default")
        self.assertEqual(config["primary_color"], "#ffd700")
        self.assertEqual(config["logo_text"], "RESEARCH_ASSOCIATE")

    def test_vancouver_theme(self):
        """Test white-label vancouver branding tokens."""
        config = self.service.get_config("vancouver")
        self.assertEqual(config["primary_color"], "#2c3e50")
        self.assertEqual(config["logo_text"], "CASCADIA_RESEARCH")
        self.assertEqual(config["mode"], "white-label")

if __name__ == "__main__":
    unittest.main()
