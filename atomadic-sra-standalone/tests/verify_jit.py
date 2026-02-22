
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.toolsmith_agent import ToolsmithAgent
from src.tools.tool_execution_layer import ToolExecutionLayer

def test_jit():
    print("=== SRA JIT Skill Loop Verification ===")
    
    agent = ToolsmithAgent()
    tool_name = "jit_test_tool"
    
    # Ensure tool doesn't exist yet
    tools_dir = "src/tools"
    path = os.path.join(tools_dir, f"{tool_name}.py")
    if os.path.exists(path):
        os.remove(path)
        print(f"[Setup] Removed existing {tool_name}")
        
    print(f"\n[Test] Attempting task requiring missing tool '{tool_name}'...")
    
    # Execute with JIT enabled
    # The 'attempt_task_with_jit' wrapper should:
    # 1. Fail to find tool
    # 2. Generate it (using the stub generator we implemented)
    # 3. Reload and retry
    
    result = agent.attempt_task_with_jit(
        task="Test JIT Loop",
        tool_name=tool_name,
        args=[]
    )
    
    print(f"[DEBUG] JIT Result: {result}")
    
    if "Executed" in str(result) and "jit_test_tool" in str(result):
        print(f"[PASS] JIT Loop Success: Result = {result}")
    else:
        print(f"[FAIL] JIT Loop returned unexpected result: {result}")
        
    # verify file exists
    if os.path.exists(path):
         print(f"[PASS] Tool file persisted at {path}")
    else:
         print(f"[FAIL] Tool file missing!")

if __name__ == "__main__":
    test_jit()
