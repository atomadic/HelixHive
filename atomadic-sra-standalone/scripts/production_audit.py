
import os
import json
import logging
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SRA-Production-Audit")

def audit_production_readiness():
    logger.info("--- SRA PRODUCTION HEALTH AUDIT v3.8.0.0 ---")
    
    # 1. Vault Health
    vault_path = "src/core/vault"
    if os.path.exists(vault_path):
        logs = [f for f in os.listdir(vault_path) if f.endswith(".json")]
        logger.info(f"[√] EvolutionVault: Found {len(logs)} state logs.")
    else:
        logger.warning("[!] EvolutionVault: Path missing or empty.")

    # 2. Leech Lattice Integrity
    coset_path = "leech_coset_leaders.npy"
    if os.path.exists(coset_path):
        data = np.load(coset_path)
        if len(data) == 4096:
            logger.info(f"[√] Leech Lattice: 4096-entry coset table VERIFIED.")
        else:
            logger.error(f"[X] Leech Lattice: Incomplete table ({len(data)}/4096).")
    else:
        logger.error("[X] Leech Lattice: Coset table missing.")

    # 3. Static Asset Manifest
    static_assets = [
        "src/server/static/manifest.json",
        "src/server/static/sw.js",
        "src/server/static/pages/research.html"
    ]
    for asset in static_assets:
        if os.path.exists(asset):
            logger.info(f"[√] Manifestation: {os.path.basename(asset)} present.")
        else:
            logger.error(f"[X] Manifestation: {os.path.basename(asset)} MISSING.")

    # 4. Security Check
    api_key = os.getenv("SRA_API_KEY")
    if api_key:
        logger.info("[√] Security: Custom SRA_API_KEY detected in environment.")
    else:
        logger.warning("[!] Security: Using default SRA_SOVEREIGN_2026 key.")

    logger.info("--- AUDIT COMPLETE ---")

if __name__ == "__main__":
    audit_production_readiness()
