
import os
import sys
import json
import hashlib

# Ensure root is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.core.evolution_vault import EvolutionVault

def test_vault_save():
    print("[Test] Initializing vault...")
    vfile = "data/test_save_vault.json"
    if os.path.exists(vfile):
        os.remove(vfile)
        
    vault = EvolutionVault(vfile)
    print(f"[Test] Vault initialized. Exists: {os.path.exists(vfile)}")
    
    with open(vfile, "r") as f:
        data = json.load(f)
        sig = data["metadata"].get("sovereign_signature")
        print(f"[Test] Sovereign Signature (V2): {sig[:32]}...")
        assert len(sig) == 128, "Sig length mismatch (should be SHA3-512)"
    
    print("[Test] SUCCESS")

if __name__ == "__main__":
    try:
        test_vault_save()
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
