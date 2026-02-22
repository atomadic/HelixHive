import os
import re
import sys

# Configuration
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRA_MD = os.path.join(ROOT_DIR, 'sra.md')
AGENTS = [
    'sra-ide-orchestrator.md',
    'sra-code-architect.md',
    'sra-ui-designer.md',
    'sra-tester-validator.md',
    'sra-deployer.md'
]
EXPECTED_VERSION = "v3.2.1.0"

def get_version(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'v(\d+\.\d+\.\d+\.\d+)', content)
    if match:
        return match.group(1)
    return None

def check_consistency():
    print(f"Checking consistency for SRA {EXPECTED_VERSION} in {ROOT_DIR}...\n")
    
    # Check sra.md
    if not os.path.exists(SRA_MD):
        print(f"[FAIL] sra.md not found at {SRA_MD}")
        return False
    
    sra_version = get_version(SRA_MD)
    if sra_version != EXPECTED_VERSION.strip('v'):
        print(f"[FAIL] sra.md version mismatch. Found {sra_version}, expected {EXPECTED_VERSION}")
    else:
        print(f"[OK] sra.md is {EXPECTED_VERSION}")

    # Check Agents
    all_pass = True
    for agent in AGENTS:
        path = os.path.join(ROOT_DIR, agent)
        if not os.path.exists(path):
            print(f"[FAIL] Agent file missing: {agent}")
            all_pass = False
            continue
            
        version = get_version(path)
        if version != EXPECTED_VERSION.strip('v'):
             print(f"[FAIL] {agent} version mismatch. Found {version}, expected {EXPECTED_VERSION}")
             all_pass = False
        else:
            print(f"[OK] {agent} is {EXPECTED_VERSION}")
            
    return all_pass

if __name__ == "__main__":
    if check_consistency():
        print("\nAll SRA components are consistent.")
        sys.exit(0)
    else:
        print("\nConsistency check FAILED.")
        sys.exit(1)
