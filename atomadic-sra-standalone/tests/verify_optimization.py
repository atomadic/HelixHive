
import sys
import os
import time

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.optimization_agent import OptimizationAgent

def create_slow_script():
    content = """
import time

def slow_fib(n):
    if n <= 1:
        return n
    # Inefficient recursive implementation
    return slow_fib(n-1) + slow_fib(n-2)

if __name__ == "__main__":
    start = time.time()
    # 30 is large enough to be slowish (~0.3s) but not freeze testing
    print(f"Fib(30) = {slow_fib(30)}")
    print(f"Time taken: {time.time() - start:.4f}s")
"""
    path = os.path.abspath("tests/slow_fib_target.py")
    with open(path, "w") as f:
        f.write(content)
    return path

def test_optimization():
    print("=== SRA Optimization Engine Verification ===")
    
    # 1. Setup Slow Script
    target_path = create_slow_script()
    print(f"[Setup] Created slow target: {target_path}")
    
    # 2. Run Optimization Agent
    agent = OptimizationAgent()
    print("\n[Test] Requesting optimization...")
    result = agent.optimize_file(target_path)
    
    if result["status"] == "success":
        opt_path = result["optimized"]
        print(f"[PASS] Optimization loop completed.")
        print(f"       Original: {result['original']}")
        print(f"       Optimized: {opt_path}")
        
        # 3. Verify Optimized File Content (Basic Check)
        with open(opt_path, "r") as f:
            content = f.read()
            print("\nPreview of Optimized Code:")
            print("-" * 40)
            print(content[:500] + "..." if len(content) > 500 else content)
            print("-" * 40)
            
            # Heuristic check: Did it memoize or use iterative?
            # We hope the LLM did something smart.
            if "memo" in content or "range" in content or "while" in content:
                print("[PASS] Code structure suggests optimization (iterative or memoized).")
            else:
                print("[NOTE] Code structure check inconclusive (review manually).")
    else:
        print(f"[FAIL] Optimization failed: {result.get('message')}")

if __name__ == "__main__":
    test_optimization()
