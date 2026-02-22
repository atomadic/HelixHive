
import time
import sys
import os
import random
import json

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.ml_hub import MLHub
from src.agents.luminary_base import LuminaryBase
from src.agents.goal_engine import GoalEngine
from src.tools.hti_layer import HTILayer
from src.logging.structured_logger import StructuredLogger

class AutonomousEvolution:
    """
    SRA Autonomous Evolution Loop (v-Omega)
    Implements the infinite O = P(O) loop for real-world interaction and self-refinement.
    """
    def __init__(self):
        self.hub = MLHub()
        self.hti = HTILayer()
        self.logger = StructuredLogger()
        self.running = True
        
        # Initialize Core Pillars
        self.luminary = LuminaryBase("SRA-Prime")
        self.goals = GoalEngine()
        
        # UI Bridge Integration (Added Phase 12)
        from src.ui.ui_bridge import UIBridge
        self.bridge = UIBridge()
        
        # Register modules in MLHub for UI awareness
        self.hub.register_module("SRA-Prime", self.luminary)
        self.hub.register_module("GoalEngine", self.goals)
        
    def step(self):
        """A single iteration of the evolution loop."""
        print(f"\n[Evolution] Cycle Started at {time.strftime('%H:%M:%S')}")
        
        # 1. Sensory Input (Simulated environmental scan or research)
        queries = ["latest AI safety research", "autopoietic system benchmarks", "sovereign computing trends"]
        query = random.choice(queries)
        print(f"[Evolution] Procuring intelligence on: {query}")
        
        intel = self.hti.web_research_deep_dive(query)
        
        # 2. Objective Refinement (GDGA)
        alignment = self.goals.check_alignment(query)
        self.goals.apply_gdga("G-LAUNCH", alignment)
        
        # 3. Action / Fabrication (Placeholder for JIT tool or code refinement)
        # In a real run, this would invoke Toolsmith or RSI adaptation
        
        # 4. Homeostasis (AIH)
        surprise = random.uniform(0, 0.2) # Low surprise for stable launch
        self.luminary.apply_aih(surprise)
        
        # 5. Sovereignty Sync
        self.hub.perform_system_sync()
        
        # 6. UI Persistence (Aggregating state for Command Center)
        self.bridge.aggregate_state(self.hub, self.goals)
        
        # 7. Wisdom Mass delta
        self.luminary.wisdom_mass += 1
        self.logger.log_event("EvolutionLoop", "CYCLE_COMPLETE", {
            "query": query,
            "tau": round(self.luminary.tau, 4),
            "wisdom_mass": self.luminary.wisdom_mass
        })

    def run(self, max_cycles=None):
        """Run the loop."""
        cycles = 0
        try:
            while self.running:
                self._poll_commands()
                self.step()
                cycles += 1
                if max_cycles and cycles >= max_cycles:
                    break
                time.sleep(10) # 10s delay between evolution steps
        except KeyboardInterrupt:
            print("[Evolution] Interrupted by Sovereign User.")
    
    def _poll_commands(self):
        """Poll for user commands from the UI."""
        command_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'status', 'commands.json'))
        if not os.path.exists(command_file):
            return
            
        try:
            with open(command_file, "r", encoding="utf-8") as f:
                commands = json.load(f)
            
            if not commands:
                return
                
            print(f"[Evolution] Processing {len(commands)} user commands...")
            for cmd in commands:
                action = cmd.get("action")
                print(f"[Evolution] EXEC: {action}")
                if action == "AUDIT":
                    self.hub.perform_system_sync()
                    self.logger.log_event("SRA-Prime", "MANUAL_AUDIT", {"status": "SUCCESS"})
                elif action == "EVO_TOGGLE":
                    # Placeholder for more complex state changes
                    pass
            
            # Clear processed commands
            with open(command_file, "w", encoding="utf-8") as f:
                json.dump([], f)
                
        except Exception as e:
            print(f"[Evolution] Command verification failed: {e}")
        
if __name__ == "__main__":
    evo = AutonomousEvolution()
    # Continuous operation for official launch
    evo.run(max_cycles=None)
