
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.toolsmith_agent import ToolsmithAgent
from src.tools.tool_execution_layer import ToolExecutionLayer

def test_toolsmith():
    print("=== SRA Toolsmith Verification ===")
    
    # 1. Initialize Agent
    agent = ToolsmithAgent()
    
    # 2. Request Tool Fabrication
    tool_name = "multiplication_tool"
    code_content = '''
class MultiplicationTool:
    """
    Multiplies two numbers.
    """
    def execute(self, a, b):
        return a * b
'''
    print(f"\n[Test] Requesting creation of {tool_name}...")
    result = agent.generate_new_tool(tool_name, "Multiplies numbers", [], code_content=code_content)
    
    if result["status"] != "success":
        print(f"[FAIL] Tool creation failed: {result}")
        return
        
    print(f"[PASS] Tool created at: {result['path']}")
    
    # 3. Verify Load & Execution
    print("\n[Test] Loading dynamic tools...")
    layer = ToolExecutionLayer()
    layer.load_dynamic_tools()
    
    # Verify module valid
    import src.tools.multiplication_tool as mt
    tool_instance = mt.MultiplicationTool()
    calc_result = tool_instance.execute(5, 7)
    
    expected = 35
    if calc_result == expected:
        print(f"[PASS] Execution verified: 5 * 7 = {calc_result}")
    else:
        print(f"[FAIL] Execution mismatch: expected {expected}, got {calc_result}")

if __name__ == "__main__":
    test_toolsmith()
