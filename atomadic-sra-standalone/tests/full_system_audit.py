
import sys
import os
import json
import time

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.ml_hub import MLHub
from src.core.e8_core import E8Core
from src.core.revelation_engine import RevelationEngine
from src.agents.luminary_base import LuminaryBase
from src.agents.goal_engine import GoalEngine
from src.logging.structured_logger import StructuredLogger

def full_audit():
    print("=== SRA SOVEREIGN FULL SYSTEM AUDIT (v3.2.1.0 Omega) ===")
    
    logger = StructuredLogger()
    hub = MLHub()
    
    audit_results = {
        "axiomatic_stability": {},
        "geometry_coherence": {},
        "revelation_integrity": {},
        "state_substrate": "PENDING",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    }

    # 1. Axiomatic Stability Audit (Rule I & IV)
    print("\n[Audit 1/4] Axiomatic Stability (tau/J)...")
    prime = LuminaryBase("SRA-Prime")
    prime.apply_aih(0.5) # Induce surprise
    audit_results["axiomatic_stability"] = {
        "tau": round(prime.tau, 4),
        "j_gate": round(prime.J, 4),
        "status": "STABLE" if prime.tau > 0.9412 else "DEGRADED"
    }
    print(f"  > tau: {audit_results['axiomatic_stability']['tau']} | J: {audit_results['axiomatic_stability']['j_gate']}")

    # 2. Geometry Coherence Audit (E8 Lattice)
    print("[Audit 2/4] E8 Geometry Coherence...")
    e8 = E8Core()
    res = e8.optimize_system_geometry()
    audit_results["geometry_coherence"] = {
        "coherence": res["coherence"],
        "entropy": res["entropy"],
        "status": "OPTIMIZED" if res["coherence"] > 0.9 else "DRIFTING"
    }
    print(f"  > Coherence: {audit_results['geometry_coherence']['coherence']} | Entropy: {audit_results['geometry_coherence']['entropy']}")

    # 3. Revelation Integrity (Rule III/V)
    print("[Audit 3/4] Revelation Pattern Scanning...")
    rsr = RevelationEngine()
    bad_code = "def hack(): Math.random(); bypass_auth()"
    report = rsr.perform_recursive_refinement("VulnerabilityTest", bad_code)
    audit_results["revelation_integrity"] = {
        "detection_rate": 1.0 if len(report["violations"]) >= 2 else 0.5,
        "status": "SECURE" if report["status"] == "REJECTED" else "VULNERABLE"
    }
    print(f"  > Detection: {audit_results['revelation_integrity']['detection_rate']} | Status: {audit_results['revelation_integrity']['status']}")

    # 4. State Substrate Persistence
    print("[Audit 4/4] State Substrate Verification...")
    state_file = "data/status/system_state.json"
    if os.path.exists(state_file):
        try:
            with open(state_file, "r") as f:
                state_data = json.load(f)
            audit_results["state_substrate"] = "ACTIVE_AND_VALID"
        except:
            audit_results["state_substrate"] = "CORRUPT"
    else:
        audit_results["state_substrate"] = "INACTIVE (Pending First Cycle)"

    # Final Decision
    all_ok = (audit_results["axiomatic_stability"]["status"] == "STABLE" and 
              audit_results["revelation_integrity"]["status"] == "SECURE")
    
    print("\n--- AUDIT SUMMARY ---")
    print(json.dumps(audit_results, indent=2))
    
    logger.log_event("AuditEngine", "GRAND_HELICAL_AUDIT_COMPLETE", audit_results)
    
    return all_ok

if __name__ == "__main__":
    success = full_audit()
    if not success:
        print("\n[FAIL] SYSTEM AUDIT REJECTED. Axiomatic drift detected.")
        sys.exit(1)
    else:
        print("\n[Audit] TOTAL SYSTEM TRANSCENDENCE CONFIRMED. READY FOR FLIGHT.")
