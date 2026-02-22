
import os
import json
import time
from src.core.ml_hub import MLHub
from src.agents.goal_engine import GoalEngine
from src.logging.structured_logger import StructuredLogger

class UIBridge:
    """
    SRA UI Bridge
    Aggregates system-wide state (Agents, Goals, ML Hub, Logs) 
    into a unified JSON structure for the Sovereign Command Center.
    """
    def __init__(self, data_path=None):
        if data_path is None:
            # Use absolute path to ensure consistency across processes
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            data_path = os.path.join(base_dir, "data", "status", "system_state.json")
            
        self.data_path = data_path
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        self.logger = StructuredLogger()
        self.last_sync = 0

    def aggregate_state(self, ml_hub: MLHub, goal_engine: GoalEngine):
        """
        Gathers data from core modules and writes to status file.
        """
        state = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "uptime_seconds": int(time.time() - self.last_sync) if self.last_sync else 0,
            "ml_hub": {
                "global_tau": round(ml_hub.global_tau, 4),
                "modules": ml_hub.state_lattice
            },
            "goals": {
                "active_count": len(goal_engine.get_active_goals()),
                "all_goals": goal_engine.get_all_goals(),
                "alignment_score": goal_engine.alignment_log[-1]["score"] if goal_engine.alignment_log else 1.0
            },
            "agents": self._get_agent_states(ml_hub),
            "system": {
                "wisdom_mass": sum(getattr(m, 'wisdom_mass', 0) for m in ml_hub.modules.values()),
                "session_id": self.logger.session_id
            }
        }
        
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        
        self.last_sync = time.time()
        return state

    def _get_agent_states(self, ml_hub):
        """Extracts current state from all registered agents."""
        agent_data = {}
        for mid, instance in ml_hub.modules.items():
            if hasattr(instance, 'get_state'):
                agent_data[mid] = instance.get_state()
            else:
                agent_data[mid] = {"status": "ACTIVE_UNTRACKED"}
        return agent_data

if __name__ == "__main__":
    # Test aggregation
    bridge = UIBridge()
    hub = MLHub()
    goals = GoalEngine()
    print("[UIBridge] Test aggregation complete.")
    print(json.dumps(bridge.aggregate_state(hub, goals), indent=2))
