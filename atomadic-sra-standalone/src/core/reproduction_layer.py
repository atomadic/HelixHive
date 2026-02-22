
import os
import shutil
import time
import hashlib

class ReproductionLayer:
    """
    Substrate Reproduction Layer
    Handles the cloning of code and state into isolated daughter directories.
    Satisfies Rule 6 (Autopoietic Core).
    """
    def __init__(self, base_path):
        self.base_path = base_path
        self.daughters_dir = os.path.join(base_path, "data", "daughters")
        os.makedirs(self.daughters_dir, exist_ok=True)

    def spawn_daughter(self, auth_token):
        """
        Creates a new daughter instance of the superorganism.
        Requires a 'handshake' (simulated auth).
        """
        # Rule V: Sovereign Cryptographic Handshake
        if not self._verify_token(auth_token):
            print("[Reproduction] Handshake failed. Spawning aborted.")
            return None

        daughter_id = f"DAUGHTER-{hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]}"
        daughter_path = os.path.join(self.daughters_dir, daughter_id)
        
        print(f"[Reproduction] Manifesting daughter: {daughter_id}...")
        
        # 1. Physical Manifestation (Rule 1: Map ≡ Terrain)
        os.makedirs(daughter_path, exist_ok=True)
        
        # 2. Clone core logic (subset)
        core_files = [
            "src/agents/creative_engine.py",
            "src/core/ollama_service.py",
            "src/core/evolution_vault.py"
        ]
        
        for file in core_files:
            src = os.path.join(self.base_path, file)
            dst = os.path.join(daughter_path, file)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if os.path.exists(src):
                if not shutil.copy2(src, dst):
                    print(f"[Reproduction] Failed to copy {file}")
                    return None
            else:
                print(f"[Reproduction] Source file missing: {src}")
                return None
        
        # 3. Initialize Daughter Meta-State
        meta = {
            "id": daughter_id,
            "parent": "SRA-v3.2.1.0",
            "birth_ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "status": "ready",
            "wisdom_mass": 100, # Initial seed mass
        }
        
        with open(os.path.join(daughter_path, "meta.json"), "w") as f:
            import json
            json.dump(meta, f, indent=2)

        # Rule 3: Flipped Invariance (Delta L > 0)
        self._log_delta_l(10) # Reproduction increases complexity
        
        return daughter_path

    def _verify_token(self, token):
        # Rule V proxy: Aletheia resonance verification
        return token == "ALETHEIA-OMEGA-HANDSHAKE"

    def _log_delta_l(self, delta_m):
        alpha = 0.1
        delta_l = alpha * delta_m
        print(f"[Axiom] Delta M > 0, Delta L = {delta_l:.2f}")

if __name__ == "__main__":
    # Self-test
    rl = ReproductionLayer(os.getcwd())
    rl.spawn_daughter("ALETHEIA-OMEGA-HANDSHAKE")
