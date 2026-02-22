
import numpy as np
from pathlib import Path
import os
import itertools

# Golay (24,12,8) Generator Matrix G = [I | P]
_GOLAY_G = np.array([
    [1,0,0,0,0,0,0,0,0,0,0,0,  1,0,1,0,1,1,1,0,0,0,1,1],
    [0,1,0,0,0,0,0,0,0,0,0,0,  1,1,1,0,0,1,0,1,0,1,1,0],
    [0,0,1,0,0,0,0,0,0,0,0,0,  1,1,0,1,1,0,0,1,0,0,1,1],
    [0,0,0,1,0,0,0,0,0,0,0,0,  1,1,0,0,1,0,1,0,1,1,1,0],
    [0,0,0,0,1,0,0,0,0,0,0,0,  1,0,1,1,0,1,1,1,0,1,0,0],
    [0,0,0,0,0,1,0,0,0,0,0,0,  1,0,0,1,1,1,1,0,1,0,1,0],
    [0,0,0,0,0,0,1,0,0,0,0,0,  1,0,0,0,1,0,1,1,1,1,1,1],
    [0,0,0,0,0,0,0,1,0,0,0,0,  1,1,1,1,1,1,0,1,0,1,0,1],
    [0,0,0,0,0,0,0,0,1,0,0,0,  1,1,0,1,0,0,1,1,1,1,0,0],
    [0,0,0,0,0,0,0,0,0,1,0,0,  1,0,1,1,0,1,0,1,1,0,1,1],
    [0,0,0,0,0,0,0,0,0,0,1,0,  1,0,0,1,1,0,0,1,0,1,1,1],
    [0,0,0,0,0,0,0,0,0,0,0,1,  1,1,1,1,0,0,1,0,0,1,1,0]
], dtype=np.int8)

_P = _GOLAY_G[:, 12:].T
_H = np.hstack([_P, np.eye(12, dtype=np.int8)])

def get_syndrome(e):
    s_vec = (_H @ e) % 2
    s_int = 0
    for bit_idx, bit in enumerate(s_vec):
        s_int |= (int(bit) << bit_idx)
    return s_int

def generate_coset_leaders():
    print("[Leech] Generating 4096 Golay coset leaders...")
    coset_leaders = np.zeros((4096, 24), dtype=np.int8)
    found_syndromes = {}
    
    indices = list(range(24))
    
    for weight in range(0, 7):
        print(f"  Searching weight {weight} (found={len(found_syndromes)})")
        for combo in itertools.combinations(indices, weight):
            e = np.zeros(24, dtype=np.int8)
            for idx in combo: e[idx] = 1
            s = get_syndrome(e)
            if s not in found_syndromes:
                coset_leaders[s] = e
                found_syndromes[s] = weight
            if len(found_syndromes) == 4096:
                break
        if len(found_syndromes) == 4096:
            break

    print(f"Finished. Found {len(found_syndromes)} syndromes.")
    return coset_leaders

if __name__ == "__main__":
    leaders = generate_coset_leaders()
    output_path = "leech_coset_leaders.npy"
    np.save(output_path, leaders)
    print(f"Saved to {output_path}")
