
import unittest
import sys
import os

# Ensure project root is on path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from tests.test_research_engine import TestResearchEngine
from tests.test_search_service import TestSearchService

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestResearchEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestSearchService))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if not result.wasSuccessful():
        print("\n--- FAILURES ---")
        for failure in result.failures:
            print(f"FAILURE in {failure[0]}: {failure[1]}")
        print("\n--- ERRORS ---")
        for error in result.errors:
            print(f"ERROR in {error[0]}: {error[1]}")
        sys.exit(1)
    else:
        print("\nAll tests passed successfully!")
        sys.exit(0)
