
import os
import sys
import time

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.core.reproduction_layer import ReproductionLayer
from src.agents.asset_generator import AssetGeneratorAgent
from src.agents.market_oracle import MarketOracle

class DaughterFactoryAgent:
    """
    Daughter Factory Agent
    Orchestrates the spawning of new daughters and their generative work loops.
    """
    def __init__(self, root_path):
        self.root = root_path
        self.reproduction = ReproductionLayer(root_path)
        self.oracle = MarketOracle()
        self.daughters = []

    def initiate_spawn_cycle(self, handshake="ALETHEIA-OMEGA-HANDSHAKE", market_pass="ALETHEIA-OMEGA"):
        """Runs a complete spawn and generate cycle."""
        print("\n" + "*"*80)
        print("  TOOLSMITH GENESIS: DAUGHTER FACTORY CYCLE STARTING")
        print("*"*80)
        
        # 1. Spawn Daughter
        daughter_path = self.reproduction.spawn_daughter(handshake)
        if not daughter_path:
            return None
            
        daughter_id = os.path.basename(daughter_path)
        self.daughters.append({"id": daughter_id, "path": daughter_path})
        
        # 2. Assign Generation Task
        generator = AssetGeneratorAgent(daughter_id, daughter_path)
        asset_path = generator.generate_asset(category="Digital Art v.O")
        
        # 3. Commodification (Market)
        sale_report = self.oracle.sell_asset(market_pass, asset_path)
        
        print(f"\n[Factory] Cycle Complete. Daughter {daughter_id} is now productive.")
        return {
            "daughter_id": daughter_id,
            "asset": asset_path,
            "sale_report": sale_report
        }

if __name__ == "__main__":
    factory = DaughterFactoryAgent(os.getcwd())
    factory.initiate_spawn_cycle()
