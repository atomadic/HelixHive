
import sys
import os
import time

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.toolsmith_agent import ToolsmithAgent
from src.tools.tool_execution_layer import ToolExecutionLayer

def main():
    print("="*60)
    print("  SRA v3.2.1.0 -- TOOLSMITH GENESIS (Autonomous Tool Creation)")
    print("="*60)
    
    # 1. Initialize Toolsmith in Sovereign Offline mode
    print("\n[Phase 1] Initializing Toolsmith (Force Offline)...")
    toolsmith = ToolsmithAgent(force_offline=True)
    layer = ToolExecutionLayer()
    
    # 2. Attempt to run a tool that DOES NOT EXIST
    tool_name = "sovereign_logic_tool"
    task_desc = "Verify the recursive stability of the Aletheia resonance layer."
    
    print(f"\n[Phase 2] Attempting to execute non-existent tool: {tool_name}")
    print(f"Task: {task_desc}")
    
    # args must be a list or tuple
    result = toolsmith.attempt_task_with_jit(task_desc, tool_name, ["stability_check", 0.95])
    
    print(f"\n[Phase 3] JIT Execution Result:")
    print(f"--> {result}")
    
    # 4. Verify the file was created
    tool_path = os.path.join("src", "tools", f"{tool_name}.py")
    if os.path.exists(tool_path):
        print(f"\n[Success] Tool manifested at: {tool_path}")
    else:
        print(f"\n[Error] Tool manifestation failed.")

    print("\n" + "="*60)
    print("  TOOLSMITH GENESIS COMPLETE -- SYSTEM CAN NOW EXPAND ITS OWN TOOLSET")
    print("="*60)

if __name__ == "__main__":
    main()
