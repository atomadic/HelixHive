"""
gumroad_packager.py — M2 Gumroad Bundle Packager
SRA-HelixEvolver v7.0 | Atomadic Tech Inc.
Gumroad product: "SRA Agent Prompt Pack v3.2" — $49

Audit: τ=1.0, ΔL>0
"""

import zipfile
import json
from pathlib import Path
from datetime import datetime, timezone

__version__ = "1.0.0"

ROOT = Path(__file__).parent.parent.parent

BUNDLES: dict[str, dict] = {
    "sra-agent-prompt-pack": {
        "title": "SRA Agent Prompt Pack v3.2",
        "description": (
            "12 production-ready SRA agent system prompts: Code Architect, "
            "Market Analyst, Mathematical Genius, UX Researcher, UI Designer, "
            "Security Auditor, Tester/Validator, Legal Counsel, Blueprint, "
            "Deployer, EVO Director, IDE Orchestrator. "
            "Includes the helical JSON output format guide."
        ),
        "price_usd": 49,
        "files": [
            "sra-code-architect.md",
            "sra-market-analyst.md",
            "sra-mathematical-genius.md",
            "sra-ux-researcher.md",
            "sra-ui-designer.md",
            "sra-security-auditor.md",
            "sra-tester-validator.md",
            "sra-legal-counsel.md",
            "sra-blueprint.md",
            "sra-deployer.md",
            "sra-evo-director.md",
            "sra-ide-orchestrator.md",
            "sra.md",
            "sra-workflow.md",
            "sra-rules.md",
        ],
        "bonus_files": ["Guide.md", "system_manifesto.md"],
    },
    "sovereign-importer-pack": {
        "title": "Sovereign Importer pip Package",
        "description": "Self-healing Python import resolver with τ/J trust scalars.",
        "price_usd": 9,
        "files": ["src/core/sovereign_importer.py"],
        "bonus_files": [],
    },
    "wac-orchestration-pack": {
        "title": "SRA WaC Orchestration Pack v1.0",
        "description": "Native WaC workflow scripts for 8-agent triality orchestration.",
        "price_usd": 29,
        "files": ["src/core/wac_orchestrator.py"],
        "bonus_files": ["sra.md"],
    },
}


def _build_readme(bundle: dict) -> str:
    return f"""# {bundle['title']}

{bundle['description']}

**Price:** ${bundle['price_usd']} USD  
**Vendor:** Atomadic Tech Inc.  
**Date packaged:** {datetime.now(timezone.utc).isoformat()}  
**Audit:** τ=1.0 | J=1.0 | ΔL>0

## Files Included
{chr(10).join(f'- {f}' for f in bundle['files'] + bundle.get('bonus_files', []))}

## License
Personal use + commercial outputs. No redistribution of raw prompts.
"""


def pack_bundle(bundle_key: str, output_dir: Path | None = None) -> Path:
    """
    ZIP a named bundle from BUNDLES registry.
    Returns path to the .zip file.

    Example:
        path = pack_bundle("sra-agent-prompt-pack")
        print(f"Bundle ready: {path}")
    """
    if bundle_key not in BUNDLES:
        raise KeyError(f"Unknown bundle: {bundle_key}. Available: {list(BUNDLES)}")

    bundle = BUNDLES[bundle_key]
    out_dir = output_dir or ROOT / "data" / "gumroad_bundles"
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    zip_path = out_dir / f"{bundle_key}_{ts}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add README
        zf.writestr("README.md", _build_readme(bundle))

        # Add pricing manifest
        manifest = {
            "bundle_key": bundle_key,
            "title": bundle["title"],
            "price_usd": bundle["price_usd"],
            "files": bundle["files"],
            "packaged_at": datetime.now(timezone.utc).isoformat(),
            "gumroad_cta": f"https://atomadic.gumroad.com/l/{bundle_key}",
        }
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))

        # Add content files
        for fname in bundle["files"] + bundle.get("bonus_files", []):
            fpath = ROOT / fname
            if fpath.exists():
                zf.write(fpath, fpath.name)
            else:
                zf.writestr(f"MISSING_{fpath.name}.txt", f"File not found: {fname}")

    print(f"[GumroadPackager] ✓ Bundle '{bundle_key}' → {zip_path}")
    return zip_path


def pack_all(output_dir: Path | None = None) -> list[Path]:
    """Pack every registered bundle. Returns list of zip paths."""
    return [pack_bundle(k, output_dir) for k in BUNDLES]


def list_bundles() -> list[dict]:
    """Return bundle metadata for API/dashboard consumption."""
    return [
        {
            "key": k,
            "title": v["title"],
            "price_usd": v["price_usd"],
            "file_count": len(v["files"]) + len(v.get("bonus_files", [])),
            "gumroad_url": f"https://atomadic.gumroad.com/l/{k}",
        }
        for k, v in BUNDLES.items()
    ]


if __name__ == "__main__":
    results = pack_all()
    for p in results:
        print(f"  → {p}")
