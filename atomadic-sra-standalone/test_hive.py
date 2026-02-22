import asyncio
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))

from src.core.hive_bridge import HiveBridge

async def test_llm():
    bridge = HiveBridge()
    print("Checking HiveBridge availability...")
    if not bridge.llm_available:
        print("HiveBridge LLM NOT available. Check HelixHive-main path and modules.")
        return

    print("Attempting Cloud LLM call...")
    resp = await bridge.call_llm("Hello, are you online?", "You are a diagnostic assistant.")
    print(f"Response: {resp}")

if __name__ == "__main__":
    asyncio.run(test_llm())
