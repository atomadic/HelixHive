
import logging
import os
import time
from typing import Dict, Any, List, Optional
from .evolution_vault import EvolutionVault

logger = logging.getLogger(__name__)

class PluginService:
    """
    SRA Plugin & Marketplace Managed Substrate.
    Handles registration, installation, and product listings.
    """
    def __init__(self, vault: EvolutionVault):
        self.vault = vault
        self.plugin_key = "plugin_registry"
        self.product_key = "marketplace_products"
        self.skills_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".agent", "rules")
        self._init_registry()
        self.discover_manifested_skills()

    def discover_manifested_skills(self):
        """Autonomously discover and map new skills in the .agent/rules directory."""
        if not os.path.exists(self.skills_dir):
            logger.warning(f"[Plugin] Skills directory not found: {self.skills_dir}")
            return

        print(f"[Plugin] Scanning for manifested skills in: {self.skills_dir}...")
        plugins = self.vault.get_state(self.plugin_key) or {}
        found_new = False

        for file in os.listdir(self.skills_dir):
            if file.endswith(".md"):
                skill_id = f"skill_{file[:-3].lower()}"
                if skill_id not in plugins:
                    print(f"[Plugin] Auto-detecting new skill: {file}")
                    plugins[skill_id] = {
                        "name": file[:-3].replace("-", " ").title(),
                        "path": os.path.join(self.skills_dir, file),
                        "type": "manifested_skill",
                        "discovered_at": time.time()
                    }
                    found_new = True

        if found_new:
            secret = os.getenv("SRA_SOVEREIGN_2026", "SRA_SOVEREIGN_2026")
            self.vault.update_state(self.plugin_key, plugins, secret=secret)

    def _init_registry(self):
        if not self.vault.get_state(self.plugin_key):
            # Seed with core plugins
            initial_plugins = {
                "core_revelation": {"name": "Core Revelation Engine", "version": "4.0.0.0", "active": True},
                "pwa_generator": {"name": "PWA Manifestation Engine", "version": "1.0.0", "active": True}
            }
            secret = os.getenv("SRA_SOVEREIGN_2026", "SRA_SOVEREIGN_2026")
            self.vault.update_state(self.plugin_key, initial_plugins, secret=secret)

    def register_product(self, product_id: str, metadata: Dict[str, Any]):
        """List a manifested product (app/insight) in the marketplace."""
        products = self.vault.get_state(self.product_key) or {}
        products[product_id] = {
            **metadata,
            "listed_at": time.time(),
            "status": "published"
        }
        secret = os.getenv("SRA_SOVEREIGN_2026", "SRA_SOVEREIGN_2026")
        self.vault.update_state(self.product_key, products, secret=secret)
        logger.info(f"[Marketplace] Listed product: {product_id}")

    def get_marketplace_data(self) -> Dict[str, Any]:
        """Retrieve full marketplace state."""
        return {
            "plugins": self.vault.get_state(self.plugin_key) or {},
            "products": self.vault.get_state(self.product_key) or {}
        }

# Revelation Engine Summary (Marketplace):
# - Epiphany: A sovereign system must have a vibrant internal economy.
# - Revelations: Extensible plugins, Manifested product listings, Vault-backed.
# - Coherence: 1.0
