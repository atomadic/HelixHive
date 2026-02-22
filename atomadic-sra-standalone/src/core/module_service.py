import os
import time
import json
import logging
import uuid
from typing import Dict, List, Optional

logger = logging.getLogger("ModuleService")

class ModuleService:
    """
    Sovereign Module Creation Engine v4.3.0.0
    Axiom: Autopoiesis (Self-Generation)
    """
    def __init__(self, vault, plugin_service):
        self.vault = vault
        self.plugin_service = plugin_service
        self.modules_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "modules"))
        self.pages_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "server", "static", "pages"))
        
        # Ensure modules directory exists
        os.makedirs(self.modules_dir, exist_ok=True)

    def manifest_module(self, module_id: str, prompt: str, features: List[str]) -> Dict:
        """
        Scaffolds a new module (Python + HTML).
        """
        logger.info(f"[Autopoiesis] Manifesting module: {module_id}")
        
        # 1. Scaffolding Python Backend (Placeholder for future LLM integration)
        py_template = f'''# {module_id} // Autopoietic Module v4.3.0.0
# Prompt: {prompt}

class {module_id.capitalize()}Module:
    def __init__(self):
        self.id = "{module_id}"
        self.features = {features}

    def execute(self):
        return {{"status": "active", "module": "{module_id}"}}

if __name__ == "__main__":
    m = {module_id.capitalize()}Module()
    print(m.execute())
'''
        py_path = os.path.join(self.modules_dir, f"{module_id}.py")
        with open(py_path, "w") as f:
            f.write(py_template)

        # 2. Scaffolding HTML Fragment
        html_template = f'''<!-- {module_id} Fragment // v4.3.0.0 -->
<div class="card" style="grid-column: span 12;">
    <h3 class="card-title">{module_id.upper()}</h3>
    <div style="margin-top: 2rem; color: #94a3b8; font-family: 'JetBrains Mono'; font-size: 0.9rem;">
        <p>Manifested via Revelation Engine.</p>
        <p>Prompt: {prompt}</p>
        <div style="margin-top: 2rem;">
            <strong>Active Features:</strong>
            <ul style="margin-top: 10px;">
                {' '.join([f'<li>{feat}</li>' for feat in features])}
            </ul>
        </div>
    </div>
    <div style="margin-top: 2rem; display: flex; gap: 1rem;">
        <button class="btn btn-evolution" onclick="showToast('Evolving {module_id}...')">EVOLVE_MODULE</button>
        <button class="btn" style="border-color: var(--neon-pink); color: var(--neon-pink);" onclick="showToast('Deprecating...')">DEPRECATE</button>
    </div>
</div>
'''
        html_path = os.path.join(self.pages_dir, f"{module_id}.html")
        with open(html_path, "w") as f:
            f.write(html_template)

        # 3. Registering with Plugin Service
        self.plugin_service.register_product(module_id, {
            "name": module_id,
            "type": "autopoietic_module",
            "url": f"/pages/{module_id}.html",
            "prompt": prompt,
            "timestamp": time.time()
        })

        self.vault.log_item("evolutions", {
            "type": "module_manifestation",
            "module_id": module_id,
            "prompt": prompt,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        })

        return {
            "status": "success",
            "module_id": module_id,
            "paths": {"py": py_path, "html": html_path}
        }

    def list_autopoietic_modules(self) -> List[Dict]:
        """Returns all modules created via this service."""
        marketplace = self.plugin_service.get_marketplace_data()
        return [p for p in marketplace.get("manifested_products", []) if p.get("type") == "autopoietic_module"]

if __name__ == "__main__":
    # Self-test block
    from src.core.evolution_vault import EvolutionVault
    from src.core.plugin_service import PluginService
    v = EvolutionVault()
    p = PluginService(v)
    ms = ModuleService(v, p)
    print(ms.manifest_module("test_analytics", "Generate a health analytics module", ["CPU Tracking", "Memory Optimization"]))
