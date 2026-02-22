
import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import time

# Use the bridge to read instead of write if needed, or just read the JSON
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STATE_FILE = os.path.join(BASE_DIR, "data", "status", "system_state.json")
COMMAND_FILE = os.path.join(BASE_DIR, "data", "status", "commands.json")
LOG_FILE = os.path.join(BASE_DIR, "data", "logs", "sra_events.jsonl")
STATIC_DIR = os.path.join(os.getcwd(), "src/server/static")

app = FastAPI(title="SRA // Sovereign Command Center v3.2.1.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/api/state")
async def get_state():
    """Returns the aggregated system state from file."""
    if not os.path.exists(STATE_FILE):
        return {"status": "initializing", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.post("/api/action")
async def trigger_action(request: Request):
    """Triggers a system action by writing to the command queue."""
    data = await request.json()
    action = data.get("action")
    print(f"[Portal] User triggered action: {action}")
    
    command = {
        "id": f"CMD-{int(time.time())}",
        "action": action,
        "details": data.get("details", {}),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z")
    }
    
    # Simple JSON queue append
    commands = []
    if os.path.exists(COMMAND_FILE):
        try:
            with open(COMMAND_FILE, "r", encoding="utf-8") as f:
                commands = json.load(f)
        except: pass
    
    commands.append(command)
    with open(COMMAND_FILE, "w", encoding="utf-8") as f:
        json.dump(commands, f, indent=2)
    
    return {"status": "QUEUED", "command": command}

@app.get("/api/logs")
async def get_api_logs():
    if not os.path.exists(LOG_FILE):
        return []
    logs = []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try: logs.append(json.loads(line))
                except: pass
    except Exception as e:
        print(f"Log Read Error: {e}")
    return logs[-100:]

def start_server(port=8080):
    print(f"[Portal] Manifesting on http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    start_server()
