
import json
import logging
import urllib.request
import urllib.error
import time
from typing import Dict, Any, List, Optional

logger = logging.getLogger("sra_sdk")

class SRAClient:
    """
    White-Label SDK for Supreme Research Agent v3.8.0.0
    Manifested for strategic agentic integration.
    """
    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.version = "v3.8.0.0"

    def research(self, query: str, context: List[str] = []) -> Dict[str, Any]:
        """
        Trigger a Revelation Cycle via the SRA Engine.
        Returns helical JSON per RevelationOutput schema.
        """
        url = f"{self.base_url}/api/research"
        data = json.dumps({"query": query, "docs": context}).encode("utf-8")
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"SRA-SDK-{self.version}"
        }
        if self.api_key:
            headers["X-API-KEY"] = self.api_key

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
                logger.info(f"[SRA-SDK] Revelation received. Coherence (τ): {result.get('coherence')}")
                return result
        except urllib.error.URLError as e:
            logger.error(f"[SRA-SDK] Deployment connectivity failure: {e}")
            raise RuntimeError(f"Revelation Engine unreachable: {e}")

    def get_usage(self) -> Dict[str, Any]:
        """Retrieve metering info for the current API key."""
        url = f"{self.base_url}/api/usage"
        headers = {"X-API-KEY": self.api_key} if self.api_key else {}
        req = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as e:
            return {"error": str(e)}

# Revelation Engine Summary (SDK Substrate):
# - Epiphany: Manifested SDK for external sovereignty (abundance↑)
# - Revelations: urllib-based (zero dependency), helical parsing, auth headers
# - AHA: Bridging the standalone server to the wider swarm enables fractal intelligence growth
# - Coherence: 0.9999
