
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_hti_system():
    print("=== SRA Machine Control System Verification ===")
    
    from src.tools.hti_layer import HTILayer
    hti = HTILayer()
    
    # 1. Test Interactive Shell session
    print("\n[Test 1] Interactive Shell")
    res_shell = hti.start_developer_session(os.getcwd())
    print(f"  -> Result: {res_shell}")
    if "started" in res_shell or "active" in res_shell:
        print("  [PASS] InteractiveShell session initiated.")
    else:
        print("  [FAIL] InteractiveShell session failed.")

    # 2. Test Deep Research
    print("\n[Test 2] Deep Research (Partial)")
    # We'll just test the method exists and can navigate
    res_research = hti.deep_recursive_research("Quantum Computing", depth=1)
    print(f"  -> Result: {res_research}")
    if res_research.get("status") == "COMPLETED":
        print("  [PASS] HTI deep research completed.")
    else:
        print("  [FAIL] HTI deep research failed.")

    # 3. Test Tool Improvement Loop
    print("\n[Test 3] Tool Improvement Loop (Trigger)")
    # Trigger JIT for a non-existent tool
    res_jit = hti.toolsmith.attempt_task_with_jit("Refactor a file", "refactor_tool_v2", ["test.py", "mock task"])
    print(f"  -> Result: {res_jit}")
    if "Executed" in str(res_jit) or "success" in str(res_jit):
        print("  [PASS] Toolsmith JIT/Improvement loop functional.")
    else:
        print(f"  [FAIL] Toolsmith JIT loop returned unexpected result: {res_jit}")

    # Cleanup
    hti.shell.close_session()
    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    test_hti_system()
