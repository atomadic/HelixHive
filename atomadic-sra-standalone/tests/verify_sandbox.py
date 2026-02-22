
import sys
import os
import time

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.sandbox_wrapper import SandboxWrapper

def test_sandbox():
    print("=== SRA Sandbox Verification ===")
    
    sandbox = SandboxWrapper(timeout_seconds=2)
    
    # 1. Test Valid Execution
    print("\n[Test 1] Valid simple calculation...")
    code_valid = "result = 5 * 5"
    try:
        res = sandbox.execute(code_valid)
        if res == 25:
            print("[PASS] Valid calculation returned 25")
        else:
            print(f"[FAIL] Expected 25, got {res}")
    except Exception as e:
        print(f"[FAIL] Valid execution error: {e}")

    # 2. Test Timeout
    print("\n[Test 2] Infinite Loop (Timeout)...")
    code_loop = "while True: pass"
    try:
        sandbox.execute(code_loop)
        print("[FAIL] Infinite loop was NOT caught!")
    except TimeoutError:
        print("[PASS] TimeoutError caught successfully.")
    except Exception as e:
        print(f"[FAIL] Unexpected error type: {type(e)}")

    # 3. Test Restricted Globals (File Access)
    print("\n[Test 3] Forbidden File Access...")
    code_file = "open('test.txt', 'w').write('hacked')"
    try:
        sandbox.execute(code_file)
        print("[FAIL] File access was NOT caught!")
    except NameError as e:
        if "open" in str(e):
            print("[PASS] 'open' is undefined (NameError caught).")
        else:
            print(f"[PASS] NameError caught but message differs: {e}")
    except Exception as e:
        print(f"[NOTE] Blocked with error: {e} (Acceptable)")

if __name__ == "__main__":
    test_sandbox()
