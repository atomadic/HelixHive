
import sys
import os
import json
import time

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_transparency_system():
    print("=== SRA Transparency & Accountability Verification ===")
    
    from src.agents.luminary_base import LuminaryBase
    from src.logging.structured_logger import StructuredLogger
    
    agent = LuminaryBase("Inspector")
    logger = StructuredLogger()
    
    # 1. Test Thought Stream
    print("\n[Test 1] Agent Thought Stream Logging")
    thought = "I am observing the file structure to identify potential optimization points."
    agent.thought_stream(thought, context={"target": "src/core"})
    
    # Verify log entry exists
    time.sleep(1)
    LOG_FILE = "data/logs/sra_events.jsonl"
    found = False
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if "REASONING" in line and thought in line:
                    found = True
                    break
    
    if found:
        print("  [PASS] Thought stream successfully logged to audit trail.")
    else:
        print("  [FAIL] Thought stream not found in audit trail.")

    # 2. Test Multi-Window UI Logic
    print("\n[Test 2] Dynamic UI Window Support")
    from src.ui.dynamic_output_panel import DynamicOutputPanel
    ui = DynamicOutputPanel()
    
    thought_res = ui.update_agent_thoughts("Inspector", "Refining E8 lattice projection.")
    panel_res = ui.update_panel_discussion("Core Architecture Evolution", ["Luminary", "C-Level"], "Dialogue: Proposing HoTT expansion.")
    
    if thought_res["type"] == "thought_stream" and panel_res["type"] == "panel_discussion":
        print("  [PASS] Multi-window UI logic verified.")
    else:
        print("  [FAIL] UI logic failed to differentiate window types.")

    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    test_transparency_system()
