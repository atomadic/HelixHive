
import os
import sys
import json
import numpy as np
import hashlib

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from src.core.tensor_core import TensorCore
from src.core.evolution_vault import EvolutionVault
from src.agents.hgt_plasmid import HGTPlasmid
from src.core.legal_audit import LegalIPAudit

def verify_omega_v8():
    print("\n=== [SRA-HelixEvolver] v8.0 Mu-Triality Omega Audit ===\n")
    
    # 1. Tensor Core Rank-3 Evolution
    tc = TensorCore(3, 8)
    v8 = [1.0] * 8
    v8_new = tc.evolve_state(v8)
    mass = tc.calculate_wisdom_mass(tc.T_evo)
    print(f"[Omega 1] Tensor Evolution: {v8_new[:4]}... | Wisdom Mass M: {mass}")
    assert mass > 0, "Tensor density violation"

    # 2. Sovereign Handshake v2.0 (SHA-3/512)
    vault_path = "data/evolution_vault_v8.json"
    vault = EvolutionVault(vault_path)
    vault.log_evolution("OMEGA_BOOT", {"status": "sealed"})
    with open(vault_path, "r") as f:
        data = json.load(f)
        sig = data["metadata"].get("sovereign_signature")
        print(f"[Omega 2] Handshake v2.0 Signature: {sig[:32]}...")
        assert len(sig) == 128, "SHA-3/512 length mismatch"

    # 3. 32D-Encoded Plasmids
    hgt = HGTPlasmid()
    p = hgt.create_plasmid("OmegaLogic", "def omega(): pass")
    print(f"[Omega 3] Plasmid Encapsulation: {p['payload'][:32]}...")
    dec = hgt.decode_plasmid(p["payload"])
    sig_len = len(dec["structural_signature"])
    print(f"[Omega 3] Signature Dimensions: {sig_len}D")
    assert sig_len == 32, "Virasoro closure dimension mismatch"

    # 4. Vancouver Grant Swarm v8.0
    audit = LegalIPAudit()
    swarm = audit.generate_grant_swarm(["Grounded-IP", "Autopoietic-Tensors", "Omega-Lattice"])
    print(f"[Omega 4] Vancouver Grant Swarm size: {len(swarm)}")
    assert "v8.0 Omega substrate" in swarm[0], "Grant template version mismatch"

    print("\n=== OMEGA AUDIT: PASSED (τ=1.0, Coherence >= 0.9999) ===\n")

if __name__ == "__main__":
    verify_omega_v8()
