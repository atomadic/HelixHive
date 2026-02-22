
import os
import sys
import json
import time
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SRA-Server")

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from src.core.evolution_vault import EvolutionVault
from src.core.ollama_service import OllamaService
from src.core.hive_bridge import HiveBridge
from src.agents.hive_agent_adapter import HiveAgentAdapter
from src.core.research_engine import ResearchEngine
from src.core.branding_service import BrandingService
from src.core.auth_service import AuthService
from src.core.settings_service import SettingsService
from src.core.plugin_service import PluginService
from src.core.module_service import ModuleService

app = FastAPI(title="SRA Internal IDE", version="4.4.0.0")

# Security Substrate
SRA_API_KEY = os.getenv("SRA_API_KEY", "SRA_SOVEREIGN_2026")

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Shared services
vault = EvolutionVault()
llm = OllamaService()
hive = HiveBridge()
hive_agents = HiveAgentAdapter()
settings_service = SettingsService(vault)
plugin_service = PluginService(vault)
auth_service = AuthService(vault)
branding_service = BrandingService()
research_engine = ResearchEngine(hive, vault, settings_service)
module_service = ModuleService(vault, plugin_service)
billing_service = research_engine.billing

# --- Pages -------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index():
    with open(os.path.join(static_dir, "index.html")) as f:
        return HTMLResponse(f.read())

@app.get("/evolution", response_class=HTMLResponse)
async def evolution_page():
    with open(os.path.join(static_dir, "pages", "evolution.html")) as f:
        return HTMLResponse(f.read())

@app.get("/agents", response_class=HTMLResponse)
async def agents_page():
    with open(os.path.join(static_dir, "pages", "agents.html")) as f:
        return HTMLResponse(f.read())

@app.get("/knowledge", response_class=HTMLResponse)
async def knowledge_page():
    with open(os.path.join(static_dir, "pages", "knowledge.html")) as f:
        return HTMLResponse(f.read())

@app.get("/research", response_class=HTMLResponse)
async def research_page():
    with open(os.path.join(static_dir, "pages", "research.html")) as f:
        return HTMLResponse(f.read())

@app.get("/settings", response_class=HTMLResponse)
async def settings_page():
    with open(os.path.join(static_dir, "pages", "settings.html")) as f:
        return HTMLResponse(f.read())

@app.get("/marketplace", response_class=HTMLResponse)
async def marketplace_page():
    with open(os.path.join(static_dir, "pages", "marketplace.html")) as f:
        return HTMLResponse(f.read())

# --- PWA Static Routes (Root Level) ------------------------------------------

@app.get("/billing")
async def billing_page():
    return FileResponse(os.path.join(static_dir, "pages", "billing.html"))

@app.get("/api/billing/stats")
async def get_billing_stats():
    return billing_service.get_stats("master")

@app.get("/api/branding/config")
async def get_branding_config(theme: str = "default"):
    return branding_service.get_config(theme)

@app.post("/api/app/manifest")
async def manifest_app(request: Request):
    # Rule 5: Sovereign access check
    api_key = request.headers.get("x-api-key") or request.headers.get("X-API-KEY")
    if not auth_service.verify_key(api_key):
        return JSONResponse({"error": "Auth Failure"}, status_code=401)

    body = await request.json()
    app_id = body.get("app_id", f"app_{int(time.time())}")
    prompt = body.get("prompt", "Revelation Engine Insight")
    features = body.get("features", ["Helix Intelligence", "Glassmorphic UI"])
    
    result = research_engine.app_gen.manifest_pwa(app_id, prompt, features)
    
    # Register as product in marketplace
    plugin_service.register_product(app_id, {
        "name": f"App: {app_id}",
        "type": "manifested_pwa",
        "url": result["url"],
        "prompt": prompt
    })
    
    return result

@app.get("/api/settings")
async def get_settings():
    return settings_service.get_all()

@app.post("/api/settings/update")
async def update_setting(request: Request):
    body = await request.json()
    return settings_service.update_setting(body["category"], body["key"], body["value"])

@app.get("/api/marketplace")
async def get_marketplace():
    return plugin_service.get_marketplace_data()

# --- API: Autopoiesis --------------------------------------------------------

@app.get("/api/modules/list")
async def list_modules():
    return JSONResponse(module_service.list_autopoietic_modules())

@app.post("/api/modules/manifest")
async def manifest_module(request: Request):
    body = await request.json()
    result = module_service.manifest_module(
        body["module_id"], 
        body["prompt"], 
        body.get("features", [])
    )
    return JSONResponse(result)

# --- Server Utilities --------------------------------------------------------

@app.get("/sw.js")
async def get_sw():
    with open(os.path.join(static_dir, "sw.js")) as f:
        return HTMLResponse(f.read(), media_type="application/javascript")

# --- API: Features ----------------------------------------------------------

@app.get("/api/features")
async def get_features():
    features = [
        {"name": "Toolsmith Agent", "status": "active", "desc": "JIT tool fabrication via LLM"},
        {"name": "Optimization Engine", "status": "active", "desc": "cProfile + LLM code rewriting"},
        {"name": "Opportunity Engine", "status": "active", "desc": "Strategic opportunity generation"},
        {"name": "Novelty Engine", "status": "active", "desc": "Serendipitous idea mining"},
        {"name": "Evolution Engine", "status": "active", "desc": "Architectural upgrade proposals"},
        {"name": "Creative Engine", "status": "active", "desc": "Feature brainstorming via LLM"},
        {"name": "Secure Sandbox", "status": "active", "desc": "Isolated code execution"},
        {"name": "Ollama Integration", "status": "active", "desc": "Local qwen2.5-coder:1.5b"},
        {"name": "Evolution Vault", "status": "active", "desc": "Strategic artifact persistence"},
        {"name": "Knowledge Base", "status": "active", "desc": "Searchable research entries"},
    ]
    return JSONResponse(features)

# --- API: Vault --------------------------------------------------------------

@app.get("/api/vault/{category}")
async def get_vault(category: str):
    items = vault.get_all(category)
    return JSONResponse(items)

@app.get("/api/vault")
async def get_vault_all():
    return JSONResponse(vault.get_all())

# --- API: Agents -------------------------------------------------------------

AGENT_REGISTRY = {
    "Toolsmith": {"status": "idle", "messages": []},
    "OptimizationAgent": {"status": "idle", "messages": []},
    "OpportunityEngine": {"status": "idle", "messages": []},
    "NoveltyEngine": {"status": "idle", "messages": []},
    "EvolutionEngine": {"status": "idle", "messages": []},
    "CreativeEngine": {"status": "idle", "messages": []},
}

@app.get("/api/agents")
async def list_agents():
    result = []
    for name, info in AGENT_REGISTRY.items():
        result.append({"name": name, "status": info["status"], "message_count": len(info["messages"])})
    return JSONResponse(result)

@app.post("/api/agents/{name}/message")
async def send_agent_message(name: str, request: Request):
    body = await request.json()
    msg = body.get("message", "")
    if name not in AGENT_REGISTRY:
        return JSONResponse({"error": f"Agent '{name}' not found"}, status_code=404)
    
    AGENT_REGISTRY[name]["messages"].append({"role": "user", "content": msg, "ts": time.time()})
    AGENT_REGISTRY[name]["status"] = "processing"
    
    # Use LLM to simulate agent response
    response = llm.generate_completion(f"You are {name}. Respond to: {msg}")
    reply = response if response else f"[{name}] Acknowledged."
    
    AGENT_REGISTRY[name]["messages"].append({"role": "agent", "content": reply, "ts": time.time()})
    AGENT_REGISTRY[name]["status"] = "idle"
    
    return JSONResponse({"reply": reply})

@app.get("/api/agents/{name}/messages")
async def get_agent_messages(name: str):
    if name not in AGENT_REGISTRY:
        return JSONResponse({"error": f"Agent '{name}' not found"}, status_code=404)
    return JSONResponse(AGENT_REGISTRY[name]["messages"])

# --- API: Knowledge Base -----------------------------------------------------

KB_FILE = "data/knowledge_base.json"

def _load_kb():
    if os.path.exists(KB_FILE):
        with open(KB_FILE) as f:
            return json.load(f)
    return []

def _save_kb(entries):
    os.makedirs(os.path.dirname(KB_FILE), exist_ok=True)
    with open(KB_FILE, "w") as f:
        json.dump(entries, f, indent=2)

@app.get("/api/knowledge")
async def get_knowledge():
    return JSONResponse(_load_kb())

@app.post("/api/knowledge")
async def add_knowledge(request: Request):
    body = await request.json()
    entries = _load_kb()
    entry = {
        "id": str(uuid.uuid4()),
        "title": body.get("title", "Untitled"),
        "content": body.get("content", ""),
        "tags": body.get("tags", []),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    }
    entries.append(entry)
    _save_kb(entries)
    return JSONResponse(entry)

# --- API: HelixHive Ecosystem ------------------------------------------------

@app.get("/api/hive/state")
async def get_hive_state():
    return JSONResponse(hive.get_state())

@app.get("/api/hive/agents")
async def list_hive_agents():
    return JSONResponse(hive_agents.list_agents())

@app.get("/api/hive/governance")
async def get_hive_governance():
    return JSONResponse(hive.get_governance_info())

@app.post("/api/hive/repair")
async def run_hive_repair(request: Request):
    body = await request.json()
    dry_run = body.get("dry_run", True)
    result = hive.run_self_repair(dry_run=dry_run)
    return JSONResponse(result or {"error": "Self-repair unavailable"})

# --- API: Research -----------------------------------------------------------

@app.post("/api/research")
async def run_research(request: Request):
    # API Key check via Sovereign AuthService
    api_key = request.headers.get("x-api-key") or request.headers.get("X-API-KEY")
    ua = request.headers.get("user-agent", "")
    is_browser = "Mozilla" in ua or "Postman" in ua
    
    if is_browser:
        # Browser access defaults to internal sovereign context
        api_key = SRA_API_KEY

    tenant = auth_service.verify_key(api_key)
    if not tenant:
        logger.error(f"[AUTH] Rejecting. Invalid Key='{api_key}', UA='{ua}'")
        return JSONResponse({"error": "Sovereign Auth Failure"}, status_code=401)

    # Rate Limiting
    if not auth_service.check_rate_limit(api_key):
        return JSONResponse({"error": "Sovereign Exhaustion (Rate Limit)"}, status_code=429)

    body = await request.json()
    query = body.get("query", "")
    docs = body.get("docs", [])
    
    if not query:
        return JSONResponse({"error": "Query required"}, status_code=400)
    
    result = await research_engine.conduct_research(query, docs)
    return JSONResponse(result)

# --- API: Monetization & Usage -----------------------------------------------

@app.get("/api/usage")
async def get_usage():
    """Get per-query usage and subscription status."""
    return JSONResponse({
        "status": "active",
        "tier": "Free",
        "queries_remaining": 50,
        "daily_limit": 50,
        "is_pro": False
    })

@app.post("/api/subscribe")
async def subscribe(request: Request):
    """Placeholder for Stripe subscription hook."""
    body = await request.json()
    # In a real app, this would initiate a Stripe Checkout session
    return JSONResponse({"status": "success", "message": "Subscription manifestation initiated"})

# --- API: Creative Engine ----------------------------------------------------

@app.post("/api/creative/generate")
async def creative_generate(request: Request):
    body = await request.json()
    context = body.get("context", "General improvements")
    
    prompt = (
        f"You are a creative product designer. Brainstorm an innovative new feature for an AI IDE platform. "
        f"Context: {context}. "
        "Format as JSON with keys: title, description, user_value, effort, priority."
    )
    
    response = llm.generate_completion(prompt)
    if response:
        response = response.replace("```json", "").replace("```", "").strip()
        try:
            item = json.loads(response)
            item["id"] = str(uuid.uuid4())
            item["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            vault.log_item("opportunities", {**item, "type": "feature_suggestion"})
            return JSONResponse(item)
        except json.JSONDecodeError:
            pass
    return JSONResponse({"error": "Generation failed"}, status_code=500)

# --- Server Entry ------------------------------------------------------------

if __name__ == "__main__":
    print("[SRA-IDE] Starting SRA Internal IDE on http://localhost:8420")
    uvicorn.run(app, host="0.0.0.0", port=8420)
