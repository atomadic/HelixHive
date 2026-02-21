"""
Marketplace index generator for HelixHive Phase 2.

Reads all template nodes from the database and generates a
`marketplace/README.md` file with a formatted catalog.
Each template must have:
  - id: unique identifier
  - title: display name
  - faction: faction name (e.g., "TradesSOP")
  - price: string or dict (e.g., "29" or {"sponsors_tier": "9", "one_time": "29"})
  - description: short description
  - leech_certificate: dict with "syndrome" and "hash" (optional, for display)
  - template_repo: GitHub template repo name (e.g., "helixhive-hvac-template")
"""

import os
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

# Path to marketplace directory (relative to repo root)
MARKETPLACE_DIR = Path("marketplace")
INDEX_FILE = MARKETPLACE_DIR / "README.md"


def sync_marketplace(db: Any, simulate: bool = False) -> bool:
    """
    Generate marketplace index from templates in the database.

    Args:
        db: Database adapter instance with `get_nodes_by_type` method.
        simulate: If True, do not write file, only log what would happen.

    Returns:
        True if the index file was changed (or would be changed in simulate mode).
    """
    logger.info("Syncing marketplace index")

    try:
        # Fetch all templates
        templates = db.get_nodes_by_type("Template")
        logger.debug(f"Found {len(templates)} templates")
    except Exception as e:
        logger.error(f"Failed to fetch templates from database: {e}")
        return False

    # Generate markdown content
    try:
        content = _generate_markdown(templates)
    except Exception as e:
        logger.error(f"Failed to generate marketplace markdown: {e}")
        return False

    # Ensure directory exists
    try:
        MARKETPLACE_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create marketplace directory: {e}")
        return False

    # Check if content changed
    old_content = ""
    if INDEX_FILE.exists():
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                old_content = f.read()
        except Exception as e:
            logger.warning(f"Could not read existing marketplace index: {e}")
            # Treat as no old content, will overwrite

    changed = (content != old_content)

    if changed and not simulate:
        try:
            with open(INDEX_FILE, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Marketplace index updated ({len(templates)} templates)")
        except Exception as e:
            logger.error(f"Failed to write marketplace index: {e}")
            return False
    elif changed and simulate:
        logger.info(f"Marketplace index would be updated ({len(templates)} templates)")
    else:
        logger.debug("Marketplace index unchanged")

    return changed


def _generate_markdown(templates: Dict[str, Dict]) -> str:
    """Generate the full Markdown content for the marketplace index."""
    lines = []
    lines.append("# HelixHive Agent Marketplace")
    lines.append("")
    lines.append(f"*Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}*")
    lines.append("")
    lines.append("Browse and spawn agentic templates. Each template is Leech‑certified and self‑repairing.")
    lines.append("")

    if not templates:
        lines.append("_No templates available yet. Check back soon!_")
        lines.append("")
        return "\n".join(lines)

    # Count by faction for summary
    factions = {}
    for t in templates.values():
        faction = t.get("faction", "Unknown")
        factions[faction] = factions.get(faction, 0) + 1

    lines.append("## Available Templates")
    lines.append("")
    for faction, count in sorted(factions.items()):
        emoji = _faction_emoji(faction)
        lines.append(f"- {emoji} **{faction}**: {count} template(s)")
    lines.append("")

    # Table header
    lines.append("| Name | Faction | Price | Description | Leech Status | Action |")
    lines.append("|------|---------|-------|-------------|--------------|--------|")

    # Sort templates by faction then title
    sorted_templates = sorted(
        templates.values(),
        key=lambda t: (t.get("faction", ""), t.get("title", ""))
    )

    for t in sorted_templates:
        title = t.get("title", "Unnamed")
        faction = t.get("faction", "Unknown")
        price_str = _format_price(t.get("price", {}))
        desc = t.get("description", "").strip()
        # Truncate description for table
        if len(desc) > 50:
            desc = desc[:47] + "..."
        leech_status = _format_leech_status(t.get("leech_certificate"))
        action = _format_action(t)

        emoji = _faction_emoji(faction)
        row = f"| {emoji} {title} | {faction} | {price_str} | {desc} | {leech_status} | {action} |"
        lines.append(row)

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("### How to Use")
    lines.append("")
    lines.append("1. **Free templates**: Click the spawn link to create your own copy.")
    lines.append("2. **Premium templates**: Become a [GitHub Sponsor](https://github.com/sponsors/atomadic) to unlock private repos.")
    lines.append("3. After spawning, the agent will self‑repair and configure itself automatically.")
    lines.append("")
    lines.append("All templates are Golay‑certified and Leech‑encoded for error‑free execution.")
    lines.append("")

    return "\n".join(lines)


def _faction_emoji(faction: str) -> str:
    """Return an emoji for the faction."""
    emoji_map = {
        "TradesSOP": "🔧",
        "HealthcareOps": "🏥",
        "RealEstateAgentic": "🏠",
        "MedSpaVoice": "💆",
        "NotionAgentOS": "📝",
        "General": "🤖",
    }
    return emoji_map.get(faction, "🤖")


def _format_price(price: Union[Dict, str, int, float, None]) -> str:
    """Format price information."""
    if price is None:
        return "Free"
    if isinstance(price, dict):
        parts = []
        if "sponsors_tier" in price:
            parts.append(f"${price['sponsors_tier']}/mo")
        if "one_time" in price:
            parts.append(f"${price['one_time']} one‑time")
        if parts:
            return " / ".join(parts)
        return "Free"
    elif isinstance(price, (int, float)):
        return f"${price}"
    elif isinstance(price, str):
        return price
    else:
        return "Free"


def _format_leech_status(cert: Optional[Dict]) -> str:
    """Format Leech certificate status as emoji."""
    if cert and cert.get("syndrome") == 0:
        return "✅ Certified"
    elif cert:
        return f"⚠️ Syndrome {cert.get('syndrome', '?')}"
    else:
        return "⚪ Uncertified"


def _format_action(template: Dict) -> str:
    """Generate the action link (spawn or sponsor)."""
    template_repo = template.get("template_repo")
    price = template.get("price", {})

    # If there's a one‑time price, we still use the template link;
    # the GitHub App will handle gating via sponsors.
    if template_repo:
        url = f"https://github.com/new?template_name={template_repo}&owner=atomadic"
        return f"[Spawn]({url})"
    else:
        return "–”"