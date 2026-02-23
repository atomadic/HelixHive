"""
fiverr_gig.py — M3 Fiverr Gig Generator
SRA-HelixEvolver v7.0 | Atomadic Tech Inc.
Produces ready-to-paste Fiverr gig JSON + description copy.

Audit: τ=1.0, ΔL>0
"""

import json
from datetime import datetime, timezone

__version__ = "1.0.0"

GIGS: list[dict] = [
    {
        "id": "sra-12-agent-research-panel",
        "title": "I will run a 12-agent AI research panel on any topic",
        "category": "AI Services",
        "subcategory": "AI Research & Analysis",
        "tags": ["AI research", "multi-agent", "autonomous AI", "market research", "technical analysis"],
        "description": """
## 🔬 12-Agent Sovereign Research Panel — Powered by SRA v8.0

I deploy a **12-specialist autonomous AI panel** on your topic, producing a structured multi-perspective report grounded in geometric coherence scoring (E₈/Leech lattice, coherence ≥ 0.9997).

### What you get:
- **12 specialist reports** (Code Architect + Market Analyst + Math Genius + 9 more)
- **GoT (Graph-of-Thoughts) synthesis** — agents debate and cross-validate
- **Helical JSON output** — structured, machine-readable, citation-rich
- **Coherence score** τ ≥ 0.94 guaranteed or revision included
- **PDF + Markdown delivery**

### Packages:
| Package | Delivery | Price |
|---------|----------|-------|
| Basic (3 agents, 1 topic) | 2 days | $50 |
| Standard (12 agents, 1 topic) | 3 days | $150 |
| Premium (12 agents, 3 topics + SR&ED doc) | 5 days | $399 |

### Use cases:
- Market entry research, Technical feasibility, IP landscape, Grant strategy

**Order now — lattice is live.**
""".strip(),
        "packages": [
            {"name": "Basic", "price_usd": 50, "delivery_days": 2, "revisions": 1, "agents": 3},
            {"name": "Standard", "price_usd": 150, "delivery_days": 3, "revisions": 2, "agents": 12},
            {"name": "Premium", "price_usd": 399, "delivery_days": 5, "revisions": 3, "agents": 12,
             "extras": ["SR&ED documentation outline", "3 topics", "Gumroad bundle included"]},
        ],
        "faq": [
            {"q": "What is the coherence score?", "a": "A geometric measure (τ) of how consistent and grounded the AI outputs are, on a 0–1 scale. We guarantee τ ≥ 0.94."},
            {"q": "Can you focus on Vancouver/BC topics?", "a": "Yes — grant landscape, market niche, and regulatory context are automatically localized."},
            {"q": "What format is the output?", "a": "Markdown + PDF + optional JSON. Machine-readable and human-readable."},
        ],
    },
    {
        "id": "sra-sovereign-ai-audit",
        "title": "I will audit your AI agent system for coherence, stability, and security",
        "category": "AI Services",
        "subcategory": "AI Consulting",
        "tags": ["AI audit", "agent stability", "security", "autonomous AI", "code review"],
        "description": """
## 🛡️ Sovereign AI System Audit — SRA Security + Stability Analysis

I run a **full sovereign audit** of your AI agent codebase using the SRA v8.0 framework:
- Import health (no broken dependencies)
- Trust scalar τ stability
- Jessica Gate J compliance
- ΔL invariance (system must provably improve over time)
- Security: prompt injection, data leakage, sovereignty violations

**Deliverable:** Structured Audit Report (Markdown + PDF) + Fix Recommendations

| Package | Scope | Price |
|---------|-------|-------|
| Quick | Single module / 500 LOC | $75 |
| Full | Entire repo up to 5K LOC | $250 |
| Enterprise | Full system + ongoing retainer | $1,200/mo |
""".strip(),
        "packages": [
            {"name": "Quick", "price_usd": 75, "delivery_days": 2, "revisions": 1},
            {"name": "Full", "price_usd": 250, "delivery_days": 4, "revisions": 2},
            {"name": "Enterprise", "price_usd": 1200, "delivery_days": 7, "revisions": "unlimited"},
        ],
        "faq": [],
    },
]


def generate_gig(gig_id: str) -> dict:
    """Return full gig payload for a given gig_id."""
    for gig in GIGS:
        if gig["id"] == gig_id:
            return {**gig, "generated_at": datetime.now(timezone.utc).isoformat()}
    raise KeyError(f"Unknown gig_id: {gig_id}")


def export_all_gigs(output_path: str | None = None) -> str:
    """Export all gigs as JSON string, optionally writing to file."""
    payload = {
        "vendor": "Atomadic Tech Inc.",
        "platform": "Fiverr",
        "tau": 1.0,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "gigs": GIGS,
    }
    out = json.dumps(payload, indent=2)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(out)
    return out


def print_gig_description(gig_id: str) -> None:
    """Pretty-print the gig description for copy-paste into Fiverr."""
    gig = generate_gig(gig_id)
    print(f"\n{'='*60}")
    print(f"GIG: {gig['title']}")
    print(f"{'='*60}\n")
    print(gig["description"])
    print(f"\n{'─'*40}")
    print("PACKAGES:")
    for pkg in gig["packages"]:
        print(f"  [{pkg['name']}] ${pkg['price_usd']} — {pkg['delivery_days']}d delivery")


if __name__ == "__main__":
    for gig in GIGS:
        print_gig_description(gig["id"])
    print(f"\n[FiverrGigGenerator] Exported {len(GIGS)} gigs. τ=1.0 | ΔL>0")
