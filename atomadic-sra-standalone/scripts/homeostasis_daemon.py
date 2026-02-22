
import subprocess
import time
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_cycle(cycle_id):
    print(f"\n" + "!"*80)
    print(f"  ETERNAL HOMEOSTASIS -- CYCLE #{cycle_id} STARTING")
    print("!"*80)
    
    # 1. Run Hyper-Evolution (5x5x3)
    print(f"\n[Homeostasis] Launching Hyper-Evolution Batch...")
    subprocess.run(["python", "scripts/hyper_evolution.py", "--force-offline"], check=False)
    
    # 2. Run Toolsmith Genesis Audit
    print(f"\n[Homeostasis] Launching Toolsmith Capability Audit...")
    subprocess.run(["python", "scripts/toolsmith_genesis.py"], check=False)
    
    print(f"\n[Homeostasis] Cycle #{cycle_id} Complete. Stabilizing...")
    time.sleep(5) # Homeostatic pause

def main():
    print("\n" + "#"*80)
    print("  SRA v3.2.1.0 -- ETERNAL HOMEOSTASIS PROTOCOL ACTIVATED")
    print("  SYSTEM WILL EVOLVE UNTIL EXTERNAL INTERVENTION")
    print("#"*80)
    
    cycle_id = 1
    try:
        while True:
            run_cycle(cycle_id)
            cycle_id += 1
    except KeyboardInterrupt:
        print("\n[Intervention] Homeostasis protocol suspended by operator.")

if __name__ == "__main__":
    main()
