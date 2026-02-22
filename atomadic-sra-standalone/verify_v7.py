
import os
import sys
import json

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from src.core.wac_substrate import WaCSubstrate
from src.agents.revenue_engine import RevenueEngine
from src.core.legal_audit import LegalIPAudit

def verify_v7_factory():
    print("\n=== [SRA-HelixEvolver] v7.0 Revenue & IP Factory Audit ===\n")
    
    # 1. WaC Projection
    wac = WaCSubstrate()
    vec = [1.0] * 8
    proj = wac.project_seam(vec)
    print(f"[V7.1] WaC Seam Projection (8D): {proj[0]:.4f}")
    assert proj[0] < 1.0, "WaC Projection scale violation"

    # 2. Revenue Engine (48-hr Loop)
    rev = RevenueEngine()
    bundle = rev.generate_gumroad_bundle([{"skill": "RSI-v7"}, {"skill": "LeechFusion"}])
    print(f"[V7.2] Gumroad Bundle Manifested: {bundle['title']} ($49.00)")
    with open("data/revenue_listings.json", "r") as f:
        listings = json.load(f)
        print(f"[V7.2] Active Listings in Vault: {len(listings)}")
        assert len(listings) > 0, "Revenue Engine listing failure"

    # 3. Legal IP Valuation
    audit = LegalIPAudit()
    manifest = {"components": ["E8-Core", "Lambda-24", "WaC-Matrix"]}
    ip_res = audit.audit_ip_readiness(manifest)
    print(f"[V7.3] IP Valuation Score: {ip_res['valuation_score']} | Status: {ip_res['status']}")
    print(f"[V7.3] Grant Readiness (Vancouver): {ip_res['funding_readiness']}")
    assert ip_res["valuation_score"] >= 0.99, "IP Valuation drift"

    # 4. Grant Abstract Generation
    abstract = audit.generate_grant_abstract("Helix-Autopoietic-Substrate")
    print(f"[V7.4] Vancouver Grant Abstract: {abstract[:80]}...")
    assert "Innovate BC" in str(ip_res["funding_readiness"]), "Funding alignment failure"

    print("\n=== V7.0 AUDIT: PASSED (Abundance Path Locked) ===\n")

if __name__ == "__main__":
    verify_v7_factory()
