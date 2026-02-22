
import subprocess
import time
import sys
import os

def launch_sra():
    # Force ASCII-safe environment
    print("[SRA] CORONATION: SRA STANDALONE v4.1.0.0 Absolute Governing Sovereignty")
    print("-" * 40)
    
    # Check for logs directory
    if not os.path.exists("data/logs"):
        os.makedirs("data/logs")
    
    # 1. Start the Sovereign Server (FastAPI UI)
    print("[Launch] Starting Sovereign Server on http://localhost:8420...")
    server_proc = subprocess.Popen(
        [sys.executable, "src/server/app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    
    time.sleep(3) # Wait for port binding
    
    # 2. Start the Autonomous Evolution Loop
    print("[Launch] Starting Autonomous Evolution Loop...")
    evolution_proc = subprocess.Popen(
        [sys.executable, "scripts/autonomous_evolution.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
        encoding='utf-8',
        errors='replace'
    )
    
    print("\n[SRA] SYSTEM MANIFESTED AND ACTIVE")
    print("UI Access: http://localhost:8420")
    print("Monitoring Evolution Loop (Ctrl+C to Terminate Sovereign Instance)\n")
    
    try:
        # Stream evolution logs safely and keep the main process alive
        while True:
            # Check if server is still alive
            if server_proc.poll() is not None:
                print("[Critical] Sovereign Server exited unexpectedly!")
                break
                
            line = evolution_proc.stdout.readline()
            if not line:
                if evolution_proc.poll() is not None:
                    print("[Warning] Evolution loop exited.")
                    break
                time.sleep(1)
                continue
            
            clean_line = line.strip().encode('ascii', 'ignore').decode('ascii')
            if clean_line:
                print(f"  {clean_line}")
    except KeyboardInterrupt:
        print("\n[Shutdown] Terminating Sovereign Instance...")
    finally:
        if server_proc: server_proc.terminate()
        if evolution_proc: evolution_proc.terminate()
        print("[Shutdown] SRA Standalone Decoupled.")

if __name__ == "__main__":
    launch_sra()
