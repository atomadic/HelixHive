
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.daughter_factory import DaughterFactoryAgent

def verify_expansion():
    print("--- SRA DAUGHTER FACTORY REIFICATION VERIFICATION ---")
    
    factory = DaughterFactoryAgent(os.getcwd())
    
    # Run the cycle
    result = factory.initiate_spawn_cycle(
        handshake="ALETHEIA-OMEGA-HANDSHAKE",
        market_pass="ALETHEIA-OMEGA"
    )
    
    # Validate results
    if not result:
        print("[FAILED] Cycle returned None")
        return False
        
    daughter_path = os.path.join("data", "daughters", result["daughter_id"])
    if not os.path.exists(daughter_path):
        print(f"[FAILED] Daughter directory not created: {daughter_path}")
        return False
        
    asset_path = result.get("asset")
    if not asset_path or not os.path.exists(asset_path):
        print(f"[FAILED] Asset not generated: {asset_path}")
        return False
    
    if result and result.get("sale_report"):
        print("\n[SUCCESS] Daughter Factory Expansion is REIFIED.")
        print(f"Daughter ID: {result['daughter_id']}")
        print(f"Asset Created: {result['asset']}")
        print(f"Market Revenue: \u20ac{result['sale_report']['revenue']:.2f}")
        return True
    else:
        print("\n[FAILED] Expansion cycle did not complete correctly.")
        return False

if __name__ == "__main__":
    if verify_expansion():
        sys.exit(0)
    else:
        sys.exit(1)
