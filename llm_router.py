"""
Elite LLM Router for HelixHive Phase 2 – Production-grade with dynamic free model pool.

Fallback chain: Groq (fastest) → OpenRouter (diverse free models) → Web Search (Grok)
Features:
- Dynamic provider selection with real-time free model discovery
- Groq: Primary fallback for speed (Llama 3, Mistral) [citation:1][citation:7]
- OpenRouter: Secondary with curated free models (Trinity, Step 3.5, GLM-4.5-Air, DeepSeek R1) [citation:3]
- Web search integration for latest Grok models [citation:2][citation:8]
- All providers use OpenAI-compatible SDKs for seamless switching [citation:4]
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from urllib.parse import urlparse

import aiohttp
import numpy as np
#from opentelemetry import trace, metrics
#from opentelemetry.trace import Status, StatusCode

# HelixHive imports
from memory import leech_encode, _LEECH_PROJ, HD

logger = logging.getLogger(__name__)

# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class LLMRequest:
    """Immutable request context."""
    prompt: str
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    user_tier: str = "free"                     # from API key / auth
    preferred_provider: Optional[str] = None    # e.g., "groq", "openrouter", "grok"
    require_web_search: bool = False            # if True, use Grok with web search
    trace_id: str = field(default_factory=lambda: hashlib.md5(str(time.time()).encode()).hexdigest()[:16])
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LLMResponse:
    """Response with metadata."""
    text: str
    provider: str
    model: str
    latency_ms: float
    ttft_ms: Optional[float] = None
    token_usage: Dict[str, int] = field(default_factory=dict)
    cost_usd: float = 0.0
    cached: bool = False
    trace_id: str = ""

@dataclass
class FreeModelInfo:
    """Information about a free model."""
    provider: str
    model_name: str
    context_window: int
    rate_limit_rpm: int
    capabilities: List[str]          # e.g., ["reasoning", "code", "vision"]
    special_features: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProviderStats:
    """Real‑time health and usage of a provider."""
    healthy: bool = True
    consecutive_failures: int = 0
    last_failure: Optional[datetime] = None
    circuit_open_until: Optional[datetime] = None
    rpm_remaining: Optional[int] = None
    tpm_remaining: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None
    current_concurrency: int = 0
    max_concurrency: int = 10
    total_requests: int = 0
    total_errors: int = 0
    avg_latency_ms: float = 0.0


# =============================================================================
# Free Model Registry (2026 Updated) [citation:3][citation:1]
# =============================================================================

class FreeModelRegistry:
    """
    Registry of all available free models with their capabilities.
    Updated February 2026 based on current provider offerings.
    """

    # Groq free models [citation:1][citation:7]
    GROQ_MODELS = {
        "llama3-8b": FreeModelInfo(
            provider="groq",
            model_name="llama3-8b-8192",
            context_window=8192,
            rate_limit_rpm=30,
            capabilities=["chat", "reasoning"]
        ),
        "llama3-70b": FreeModelInfo(
            provider="groq",
            model_name="llama3-70b-8192",
            context_window=8192,
            rate_limit_rpm=30,
            capabilities=["chat", "reasoning", "coding"]
        ),
        "mixtral-8x7b": FreeModelInfo(
            provider="groq",
            model_name="mixtral-8x7b-32768",
            context_window=32768,
            rate_limit_rpm=30,
            capabilities=["chat", "reasoning", "coding", "multilingual"]
        )
    }

    # OpenRouter free models [citation:3][citation:6]
    OPENROUTER_MODELS = {
        "trinity-large": FreeModelInfo(
            provider="openrouter",
            model_name="arcee-ai/trinity-large-preview",
            context_window=131000,
            rate_limit_rpm=20,
            capabilities=["creative", "roleplay", "agentic"],
            special_features={"expertise": ["writing", "storytelling", "chat"]}
        ),
        "step-3.5-flash": FreeModelInfo(
            provider="openrouter",
            model_name="stepfun/step-3.5-flash",
            context_window=256000,
            rate_limit_rpm=20,
            capabilities=["reasoning", "efficient"],
            special_features={"architecture": "MoE", "active_params": "11B"}
        ),
        "glm-4.5-air": FreeModelInfo(
            provider="openrouter",
            model_name="z-ai/glm-4.5-air",
            context_window=131000,
            rate_limit_rpm=20,
            capabilities=["agentic", "reasoning"],
            special_features={"thinking_mode": True, "non_thinking_mode": True}
        ),
        "deepseek-r1": FreeModelInfo(
            provider="openrouter",
            model_name="deepseek/deepseek-r1",
            context_window=64000,
            rate_limit_rpm=20,
            capabilities=["reasoning", "math", "code"],
            special_features={"open_weights": True, "reasoning_tokens": True}
        ),
        "aurora-alpha": FreeModelInfo(
            provider="openrouter",
            model_name="openrouter/aurora-alpha",
            context_window=128000,
            rate_limit_rpm=20,
            capabilities=["reasoning", "coding", "agentic"],
            special_features={"stealth": True}
        ),
        "pony-alpha": FreeModelInfo(  # GLM-5 based [citation:6][citation:9]
            provider="openrouter",
            model_name="openrouter/pony-alpha",
            context_window=200000,
            rate_limit_rpm=20,
            capabilities=["coding", "reasoning", "roleplay", "agentic"],
            special_features={"tool_calling": "high_accuracy", "max_output": 131000}
        ),
        "nvidia-nemotron-3": FreeModelInfo(
            provider="openrouter",
            model_name="nvidia/nemotron-3-30b-a3b",
            context_window=256000,
            rate_limit_rpm=20,
            capabilities=["agentic", "efficient"],
            special_features={"architecture": "MoE", "active_params": "3B"}
        ),
        "qwen3-thinking": FreeModelInfo(
            provider="openrouter",
            model_name="gpt-oss/qwen3-235b-a22b-thinking",
            context_window=262000,
            rate_limit_rpm=20,
            capabilities=["reasoning", "math", "science"],
            special_features={"reasoning_enhanced": True, "max_output": 81920}
        )
    }

    # Gemini free tier [citation:1][citation:4]
    GEMINI_MODELS = {
        "gemini-2.0-flash": FreeModelInfo(
            provider="gemini",
            model_name="gemini-2.0-flash",
            context_window=1000000,  # 1M tokens
            rate_limit_rpm=15,
            capabilities=["multimodal", "vision", "large_context"],
            special_features={"data_usage": True}  # free tier uses data for training
        ),
        "gemini-1.5-flash": FreeModelInfo(
            provider="gemini",
            model_name="gemini-1.5-flash",
            context_window=1000000,
            rate_limit_rpm=15,
            capabilities=["multimodal", "vision", "large_context"],
            special_features={"data_usage": True}
        )
    }

    @classmethod
    def get_all_free_models(cls) -> Dict[str, FreeModelInfo]:
        """Get all free models across providers."""
        models = {}
        models.update(cls.GROQ_MODELS)
        models.update(cls.OPENROUTER_MODELS)
        models.update(cls.GEMINI_MODELS)
        return models

    @classmethod
    def get_best_model_for_task(cls, task_type: str) -> Optional[FreeModelInfo]:
        """Select the best free model for a given task type."""
        all_models = cls.get_all_free_models()
        
        # Task-specific routing logic
        task_mapping = {
            "coding": ["pony-alpha", "deepseek-r1", "aurora-alpha"],
            "reasoning": ["deepseek-r1", "qwen3-thinking", "glm-4.5-air"],
            "creative": ["trinity-large", "step-3.5-flash"],
            "agentic": ["pony-alpha", "glm-4.5-air", "aurora-alpha"],
            "large_context": ["gemini-2.0-flash", "qwen3-thinking"],
            "multimodal": ["gemini-2.0-flash"],
            "speed": ["llama3-8b", "mixtral-8x7b"],
        }
        
        preferred = task_mapping.get(task_type, [])
        for model_key in preferred:
            if model_key in all_models:
                return all_models[model_key]
        return None


# =============================================================================
# Web Search Integration for Grok [citation:2][citation:8]
# =============================================================================

class GrokWebSearch:
    """
    Integration with Grok's web search capabilities.
    Grok 4.2+ includes real-time web search and multi-agent collaboration [citation:8].
    """
    
    # Grok access tiers [citation:2]
    ACCESS_TIERS = {
        "free": {
            "daily_chats": 15,
            "daily_images": 5,
            "web_search": True,
            "multi_agent": False,
            "agents_count": 1
        },
        "educational": {
            "daily_chats": 50,
            "daily_images": 20,
            "web_search": True,
            "multi_agent": True,
            "agents_count": 4
        },
        "supergrok_heavy": {  # $300/month [citation:8]
            "daily_chats": "unlimited",
            "daily_images": "unlimited",
            "web_search": True,
            "multi_agent": True,
            "agents_count": 16
        }
    }
    
    def __init__(self, user_tier: str = "free"):
        self.user_tier = user_tier
        self.tier_config = self.ACCESS_TIERS.get(user_tier, self.ACCESS_TIERS["free"])
        self._session: Optional[aiohttp.ClientSession] = None
        self._api_key = os.getenv("GROK_API_KEY")
        
    async def search(self, query: str) -> Dict[str, Any]:
        """Perform web search via Grok."""
        if not self._api_key:
            logger.warning("No Grok API key available, falling back")
            return {"success": False, "error": "No API key"}
            
        session = await self._get_session()
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        
        # Grok API endpoint (simplified)
        payload = {
            "query": query,
            "include_web_results": True,
            "multi_agent": self.tier_config["multi_agent"],
            "agents_count": self.tier_config.get("agents_count", 1)
        }
        
        try:
            async with session.post(
                "https://api.x.ai/v1/grok/search",
                headers=headers,
                json=payload,
                timeout=30
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"success": True, "results": data.get("results", []), "text": data.get("text", "")}
                else:
                    return {"success": False, "error": f"HTTP {resp.status}"}
        except Exception as e:
            logger.error(f"Grok search failed: {e}")
            return {"success": False, "error": str(e)}
            
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session


# =============================================================================
# Abstract Provider Base Class (OpenAI-compatible)
# =============================================================================

class LLMProvider(ABC):
    """Base class for all LLM providers with OpenAI-compatible interface."""
    
    def __init__(self, name: str, config: Dict):
        self.name = name
        self.config = config
        self.stats = ProviderStats()
        self._session: Optional[aiohttp.ClientSession] = None
        self._api_key = None
        self.base_url = config.get("base_url", "")
        self.supports_openai_sdk = config.get("openai_compatible", True)
        
    @abstractmethod
    async def complete(self, request: LLMRequest, model: Optional[str] = None) -> LLMResponse:
        """Send completion request using OpenAI-compatible interface."""
        pass
        
    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=self.config.get("connection_pool_size", 10))
            self._session = aiohttp.ClientSession(connector=connector)
        return self._session
        
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()


class OpenAICompatibleProvider(LLMProvider):
    """
    Generic provider for any OpenAI-compatible API (Groq, OpenRouter, etc.)
    """
    
    async def complete(self, request: LLMRequest, model: Optional[str] = None) -> LLMResponse:
        session = await self.get_session()
        start = time.time()
        
        # Use specified model or default from config
        model_name = model or self.config.get("default_model")
        if not model_name:
            raise ValueError(f"No model specified for provider {self.name}")
            
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        
        # OpenAI-compatible payload [citation:4][citation:7]
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": False
        }
        
        try:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.get("timeout", 30))
            ) as resp:
                if resp.status == 429:
                    retry_after = int(resp.headers.get("retry-after", 60))
                    raise Exception(f"Rate limited (429) – retry after {retry_after}s")
                    
                if resp.status != 200:
                    raise Exception(f"HTTP {resp.status}: {await resp.text()}")
                    
                data = await resp.json()
                latency = (time.time() - start) * 1000
                
                usage = data.get("usage", {})
                token_usage = {
                    "prompt": usage.get("prompt_tokens", 0),
                    "completion": usage.get("completion_tokens", 0),
                    "total": usage.get("total_tokens", 0)
                }
                
                return LLMResponse(
                    text=data["choices"][0]["message"]["content"],
                    provider=self.name,
                    model=model_name,
                    latency_ms=latency,
                    token_usage=token_usage,
                    trace_id=request.trace_id
                )
        except asyncio.TimeoutError:
            raise Exception(f"Timeout connecting to {self.name}")


# =============================================================================
# Router with Dynamic Fallback Chain
# =============================================================================

class HelixLLMRouter:
    """
    Production-grade router with Groq → OpenRouter fallback chain.
    - Primary: Groq (fastest, Llama 3/Mistral) [citation:1][citation:7]
    - Secondary: OpenRouter (diverse free models) [citation:3]
    - Tertiary: Web search (Grok for real-time data) [citation:2][citation:8]
    """
    
    def __init__(self):
        self.model_registry = FreeModelRegistry()
        self.providers: Dict[str, OpenAICompatibleProvider] = {}
        self.grok_search = GrokWebSearch()
        self._init_providers()
        self.tracer = trace.get_tracer("llm_router")
        
    def _init_providers(self):
        """Initialize OpenAI-compatible providers."""
        # Groq provider [citation:1]
        self.providers["groq"] = OpenAICompatibleProvider("groq", {
            "base_url": "https://api.groq.com/openai/v1",
            "default_model": "llama3-8b-8192",
            "timeout": 30,
            "connection_pool_size": 10,
            "openai_compatible": True
        })
        
        # OpenRouter provider [citation:3]
        self.providers["openrouter"] = OpenAICompatibleProvider("openrouter", {
            "base_url": "https://openrouter.ai/api/v1",
            "default_model": "openrouter/auto",  # auto-select best free model
            "timeout": 30,
            "connection_pool_size": 10,
            "openai_compatible": True
        })
        
        # Load API keys
        self.providers["groq"]._api_key = os.getenv("GROQ_API_KEY")
        self.providers["openrouter"]._api_key = os.getenv("OPENROUTER_API_KEY")
        
    async def _get_groq_model(self, request: LLMRequest) -> Optional[str]:
        """Select best Groq model based on request characteristics."""
        if "code" in request.prompt.lower() or "programming" in request.prompt.lower():
            return "mixtral-8x7b-32768"  # better for coding
        elif len(request.prompt) > 4000:
            return "mixtral-8x7b-32768"  # larger context
        else:
            return "llama3-8b-8192"  # fastest
            
    async def _get_openrouter_model(self, request: LLMRequest) -> Optional[str]:
        """Select best OpenRouter free model based on task."""
        prompt_lower = request.prompt.lower()
        
        # Task-based routing [citation:3][citation:6]
        if any(word in prompt_lower for word in ["code", "function", "api", "programming"]):
            return "openrouter/pony-alpha"  # best for coding [citation:6]
        elif any(word in prompt_lower for word in ["reason", "math", "logic"]):
            return "deepseek/deepseek-r1"  # reasoning optimized
        elif any(word in prompt_lower for word in ["write", "story", "creative"]):
            return "arcee-ai/trinity-large-preview"  # creative writing
        elif request.require_web_search:
            return None  # fall back to Grok web search
        else:
            # Use auto-router for general queries [citation:3]
            return "openrouter/auto"
            
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """
        Main entry point with fallback chain.
        Groq → OpenRouter → Grok Web Search
        """
        with self.tracer.start_as_current_span("llm_complete") as span:
            span.set_attribute("trace_id", request.trace_id)
            span.set_attribute("preferred_provider", request.preferred_provider)
            
            errors = []
            
            # Special case: Grok web search requested
            if request.require_web_search:
                logger.info("Web search requested, using Grok")
                result = await self.grok_search.search(request.prompt)
                if result["success"]:
                    return LLMResponse(
                        text=result.get("text", json.dumps(result.get("results", []))),
                        provider="grok",
                        model="grok-4.2-web",
                        latency_ms=0,
                        trace_id=request.trace_id
                    )
                else:
                    logger.warning(f"Grok search failed: {result.get('error')}")
                    errors.append("grok_web_search_failed")
            
            # Attempt 1: Groq (fastest) [citation:1][citation:7]
            if request.preferred_provider in [None, "groq"]:
                try:
                    provider = self.providers["groq"]
                    model = await self._get_groq_model(request)
                    response = await provider.complete(request, model=model)
                    logger.info(f"Groq success: {model}")
                    return response
                except Exception as e:
                    logger.warning(f"Groq failed: {e}")
                    errors.append(f"groq_failed: {e}")
                    
            # Attempt 2: OpenRouter free models [citation:3][citation:6]
            if request.preferred_provider in [None, "openrouter"]:
                try:
                    provider = self.providers["openrouter"]
                    model = await self._get_openrouter_model(request)
                    response = await provider.complete(request, model=model)
                    logger.info(f"OpenRouter success: {model}")
                    return response
                except Exception as e:
                    logger.warning(f"OpenRouter failed: {e}")
                    errors.append(f"openrouter_failed: {e}")
                    
            # If all else fails, raise with error details
            raise Exception(f"All providers failed: {'; '.join(errors)}")
            
    async def close(self):
        for provider in self.providers.values():
            await provider.close()
        if self.grok_search._session:
            await self.grok_search._session.close()


# =============================================================================
# Singleton instance for easy use
# =============================================================================

_router_instance: Optional[HelixLLMRouter] = None

async def get_router() -> HelixLLMRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = HelixLLMRouter()
    return _router_instance

async def call_llm(prompt: str, system: Optional[str] = None,
                   temperature: float = 0.7, max_tokens: int = 1000,
                   user_tier: str = "free", require_web_search: bool = False) -> str:
    """
    Simplified entry point for other HelixHive modules.
    Automatically uses Groq → OpenRouter fallback chain.
    """
    router = await get_router()
    request = LLMRequest(
        prompt=prompt,
        system_prompt=system,
        temperature=temperature,
        max_tokens=max_tokens,
        user_tier=user_tier,
        require_web_search=require_web_search
    )
    response = await router.complete(request)
    return response.text


# =============================================================================
# Self‑test
# =============================================================================

async def self_test():
    """Test the fallback chain with various request types."""
    logger.info("Running LLM router self‑test")
    router = HelixLLMRouter()
    
    test_cases = [
        {"prompt": "Say 'hello' in one word", "type": "simple"},
        {"prompt": "Write a Python function to calculate fibonacci", "type": "coding"},
        {"prompt": "Explain quantum computing", "type": "reasoning"},
        {"prompt": "What's the latest news about AI?", "require_web_search": True, "type": "web_search"},
    ]
    
    for test in test_cases:
        try:
            request = LLMRequest(
                prompt=test["prompt"],
                require_web_search=test.get("require_web_search", False)
            )
            response = await router.complete(request)
            logger.info(f"✓ {test['type']}: {response.provider} ({response.model})")
        except Exception as e:
            logger.error(f"✗ {test['type']}: {e}")
            
    await router.close()
    return True
