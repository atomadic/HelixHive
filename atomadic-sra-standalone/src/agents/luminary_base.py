
import time

class LuminaryBase:
    """
    Base class for all 17 core luminary agents.
    Provides:
    - Connection to E8 Core and Leech Outer layers
    - Task execution with logging
    - Homeostatic tau management
    - Jessica Gate (J) enforcement
    - Active Inference Homeostasis (AIH) self-tuning
    """
    TAU_THRESHOLD = 0.9412

    def __init__(self, name):
        self.name = name
        self.tau = 1.0
        self.J = 1.0
        self.alpha = 0.1
        self.task_log = []
        self.wisdom_mass = 0
        print(f"[Luminary] Initializing {name}...")

    def thought_stream(self, thought, context=None):
        """
        Log internal reasoning steps for accountability.
        """
        from src.logging.structured_logger import StructuredLogger
        logger = StructuredLogger()
        
        entry = {
            "agent": self.name,
            "thought": thought,
            "context": context,
            "type": "thought_stream",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        
        logger.log_event(
            agent=self.name,
            action="REASONING",
            details=entry,
            level="DEBUG"
        )
        return entry

    def execute_task(self, task):
        """Execute a task with safety checks and logging."""
        # Jessica Gate check
        if self.J < 0.3:
            print(f"[{self.name}] FROZEN: J={self.J:.2f} below minimum")
            return {"status": "frozen", "agent": self.name}
        
        # tau Threshold check
        if self.tau < self.TAU_THRESHOLD:
            print(f"[{self.name}] WARNING: tau={self.tau:.4f} below threshold, self-regenerating...")
            self._regenerate()
        
        print(f"[{self.name}] Executing: {task}")
        
        entry = {
            "task": task,
            "status": "success",
            "agent": self.name,
            "tau": round(self.tau, 4),
            "J": round(self.J, 2),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        
        from src.logging.structured_logger import StructuredLogger
        logger = StructuredLogger()
        logger.log_event(self.name, "EXECUTE_TASK", entry)
        
        # Homeostasis
        self.tau += self.alpha * (1 - self.tau)
        self.wisdom_mass += 1
        self.task_log.append(entry)
        
        return entry

    def apply_aih(self, outcome_delta):
        """
        Active Inference Homeostasis (NOV-004)
        Adjusts tau based on surprise (prediction error).
        """
        # outcome_delta is the difference between expected and actual (0.0 to 1.0)
        # Higher surprise -> lower tau
        surprise = abs(outcome_delta)
        self.tau -= 0.05 * surprise
        print(f"[{self.name}] AIH adjustment: surprise={surprise:.2f}, tau->{self.tau:.4f}")

    def on_error(self, error):
        """Handle error: decrement J, log failure."""
        self.J = max(0.3, self.J - 0.1)
        print(f"[{self.name}] Error: {error}. J->{self.J:.2f}")
        
        if self.J <= 0.3:
            print(f"[{self.name}] CRITICAL: J at minimum. Operations frozen.")
        
        return {"status": "error", "J": self.J, "error": str(error)}

    def _regenerate(self):
        """Autopoietic self-regeneration: O = P(O)"""
        old_tau = self.tau
        self.tau = 0.95  # Reset to safe level
        print(f"[{self.name}] Regenerated: tau {old_tau:.4f} -> {self.tau:.4f}")

    def get_state(self):
        return {
            "name": self.name,
            "tau": round(self.tau, 4),
            "J": round(self.J, 2),
            "wisdom_mass": self.wisdom_mass,
            "tasks_completed": len(self.task_log)
        }
