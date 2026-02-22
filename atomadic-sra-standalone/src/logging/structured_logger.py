
import json
import os
import time

class StructuredLogger:
    """
    Structured Logger
    JSONL + ELK-compatible structured logging to Evolution Vault.
    All agent actions flow through here for full audit trail.
    """
    def __init__(self, log_dir="data/logs"):
        self.log_dir = log_dir
        self.log_file = os.path.join(log_dir, "sra_events.jsonl")
        os.makedirs(log_dir, exist_ok=True)
        self.session_id = f"SES-{int(time.time())}"
        self.event_count = 0

    def log_event(self, agent, action, details=None, level="INFO"):
        """Log a structured event."""
        self.event_count += 1
        event = {
            "@timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "session_id": self.session_id,
            "event_id": f"EVT-{self.event_count:06d}",
            "level": level,
            "agent": agent,
            "action": action,
            "details": details or {},
        }
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
        
        # UI/Console output sanitization
        prefix_map = {"INFO": "i", "WARN": "!", "ERROR": "X", "DEBUG": "d"}
        prefix = prefix_map.get(level, "*")
        
        safe_agent = agent.encode('ascii', 'ignore').decode('ascii')
        safe_action = action.encode('ascii', 'ignore').decode('ascii')
        
        print(f"[Log {prefix}] {safe_agent} -> {safe_action}")
        return event

    def log_agent_action(self, agent, action, input_data=None, output_data=None):
        """Convenience for logging agent actions with I/O."""
        return self.log_event(agent, action, {
            "input": str(input_data)[:200] if input_data else None,
            "output": str(output_data)[:200] if output_data else None
        })

    def log_error(self, agent, error, context=None):
        """Log an error event."""
        return self.log_event(agent, "ERROR", {
            "error": str(error),
            "context": context
        }, level="ERROR")

    def log_metric(self, agent, metric_name, value):
        """Log a metric event."""
        return self.log_event(agent, f"METRIC:{metric_name}", {
            "value": value
        }, level="INFO")

    def get_recent(self, count=20):
        """Get the most recent log entries."""
        if not os.path.exists(self.log_file):
            return []
        
        with open(self.log_file, "r") as f:
            lines = f.readlines()
        
        entries = []
        for line in lines[-count:]:
            try:
                entries.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                pass
        return entries

    def apply_tbpt(self, agent_name, error_timestamp):
        """
        Temporal Back-Prop of Trust (NOV-014)
        Identifies 'bad seeds' in historic reasoning by propagating 
        trust adjustments backwards through the event trail.
        """
        print(f"[Logger] Applying TBPT for {agent_name} (Source: {error_timestamp})")
        # In this prototype, we simulate back-propagation by identifying 
        # preceding reasoning steps and logging a trust drainage event.
        drain_event = self.log_event("SovereignAudit", "TRUST_DRAINAGE", {
            "target_agent": agent_name,
            "root_cause_timestamp": error_timestamp,
            "backprop_depth": 5,
            "delta_tau": -0.15
        }, level="WARN")
        return drain_event

    def get_stats(self):
        """Get logging statistics."""
        return {
            "session_id": self.session_id,
            "total_events": self.event_count,
            "log_file": self.log_file
        }
