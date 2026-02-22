
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_mock_service():
    print("=== SRA OllamaMock Verification ===")
    
    from src.core.ollama_service import OllamaService
    
    # Initialize with mock enabled
    service = OllamaService(use_mock=True)
    
    # 1. Test Connection
    print("\n[Test 1] Connection Check")
    is_connected = service.check_connection()
    print(f"  -> Connected: {is_connected}")
    if is_connected:
        print("  [PASS] Mock connection verified.")
    else:
        print("  [FAIL] Mock connection failed.")

    # 2. Test Tool Generation (Mock)
    print("\n[Test 2] Mock Tool Generation")
    prompt = "Create a tool named 'test_mock_tool' that sums two numbers."
    response = service.generate_completion(prompt)
    print(f"  -> Response: {response[:100]}...")
    if "class TestMockTool" in response:
        print("  [PASS] Mock tool generation verified.")
    else:
        print("  [FAIL] Mock response did not contain expected class.")

    # 3. Test General Reasoning (Mock)
    print("\n[Test 3] Mock General Reasoning")
    prompt = "What should we do next?"
    response = service.generate_completion(prompt)
    print(f"  -> Response: {response}")
    if "recursive audit loop" in response.lower():
        print("  [PASS] Mock reasoning verified.")
    else:
        print("  [FAIL] Mock response unexpected.")

    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    test_mock_service()
