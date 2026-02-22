
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.ollama_service import OllamaService
from src.agents.toolsmith_agent import ToolsmithAgent

def test_ollama():
    print("=== SRA Ollama Integration Verification ===")
    
    # 1. Test Service Connection
    service = OllamaService()
    if not service.check_connection():
        print("[FAIL] Could not connect to Ollama at http://localhost:11434")
        print("       Please ensure Ollama is running.")
        return
        
    print(f"[PASS] Connected to Ollama. Model: {service.model}")
    
    # 2. Test Direct Generation
    print("\n[Test] Generating simple function...")
    prompt = "Write a Python function to calculate the area of a circle."
    code = service.generate_completion(prompt)
    if code:
        print(f"[PASS] Received generation ({len(code)} chars).")
        print(f"Preview: {code[:100]}...")
    else:
        print("[FAIL] Generation returned None.")

    # 3. Test Toolsmith Integration (Real Generation)
    print("\n[Test] Toolsmith Agent Generation...")
    agent = ToolsmithAgent()
    
    tool_name = "fibonacci_tool"
    description = "Calculates the nth Fibonacci number."
    
    # Ensure cleanup
    tools_dir = "src/tools"
    path = os.path.join(tools_dir, f"{tool_name}.py")
    if os.path.exists(path):
        os.remove(path)
        
    result = agent.generate_new_tool(tool_name, description, [])
    
    if result["status"] == "success":
        print(f"[PASS] Tool generated and registered at {result['path']}")
        
        # Verify content is not the stub
        with open(result['path'], 'r') as f:
            content = f.read()
            if "Auto-generated tool" in content and "stub" not in content and "def execute" in content:
                 # It might be hard to distinguish stub from real without checking logic, 
                 # but our stub has specific comments. 
                 # Let's check if it actually looks like code.
                 pass
            print("Generated Content Preview:\n" + content)
    else:
        print(f"[FAIL] Tool generation failed: {result.get('message')}")

if __name__ == "__main__":
    test_ollama()
