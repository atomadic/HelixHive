
import unittest
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.demo_service import DemoService

class TestDemoService(unittest.TestCase):
    def setUp(self):
        self.service = DemoService(is_demo_mode=True)

    def test_tailored_alerts(self):
        """Test that demo mode injects Vancouver alerts."""
        alerts = self.service.get_tailored_alerts("some query")
        self.assertGreaterEqual(len(alerts), 2)
        # Check for Vancouver keywords
        has_vancouver = any("vancouver" in a.lower() or "ubc" in a.lower() or "bc tech" in a.lower() for a in alerts)
        self.assertTrue(has_vancouver)

    def test_tailored_proposals(self):
        """Test that demo mode injects tailored proposals."""
        proposals = self.service.get_tailored_proposals("some query")
        self.assertEqual(len(proposals), 2)
        self.assertTrue(any("vancouver" in p.lower() or "cascadia" in p.lower() for p in proposals))

    def test_disabled_demo_mode(self):
        """Test that no alerts are returned when demo mode is disabled."""
        disabled_service = DemoService(is_demo_mode=False)
        self.assertEqual(len(disabled_service.get_tailored_alerts("query")), 0)
        self.assertEqual(len(disabled_service.get_tailored_proposals("query")), 0)

if __name__ == "__main__":
    unittest.main()
