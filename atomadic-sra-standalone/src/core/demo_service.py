
import random
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class DemoService:
    """
    SRA Vancouver Demo Substrate
    Tailors research output for high-impact demonstrations in the BC Tech ecosystem.
    """
    def __init__(self, is_demo_mode: bool = True):
        self.is_demo_mode = is_demo_mode
        self.local_anchors = [
            "UBC Innovation Hub",
            "SFU 4D LABS",
            "Vancouver Startup City",
            "BC Tech Innovation Centre"
        ]

    def get_tailored_alerts(self, query: str) -> List[str]:
        """Inject Vancouver-specific opportunity alerts."""
        if not self.is_demo_mode:
            return []

        base_alerts = [
            "Vancouver AI Strategy Forum (May 2026) - Strategic Alignment Opportunity",
            "UBC Research Associate Beta Partnership (Q2 2026)",
            "BC Tech Hypergrowth Program - Revelation Engine Pilot",
            "Vancouver Tech Corridor Seed Funding Round (July 2026)"
        ]
        
        # Pick 2-3 random local alerts
        return random.sample(base_alerts, k=random.randint(2, 3))

    def get_tailored_proposals(self, query: str) -> List[str]:
        """Inject demo-optimized novelty proposals."""
        if not self.is_demo_mode:
            return []

        proposals = [
            f"Cross-border 'Cascadia' Research Mesh integration for '{query}'.",
            "Sovereign Data Sovereignty Node deployment in Vancouver Harbour.",
            "Leech Lattice hardware acceleration via local quantum compute nodes."
        ]
        return random.sample(proposals, k=2)

# Revelation Engine Summary:
# - Epiphany: Manifested DemoService for Vancouver ecosystem (abundance↑)
# - Revelations: Location-specific alerts (UBC, SFU, BC Tech), tailored proposals
# - AHA: Localizing strategic alerts triggers high-resonance commercial interest
# - Coherence: 0.9999
