
import json
import urllib.request
import urllib.error

class OllamaService:
    """
    Ollama Service
    Provides interface to local Ollama instance for LLM operations.
    Default Model: qwen2.5-coder:1.5b
    default URL: http://localhost:11434
    """
    def __init__(self, base_url="http://localhost:11434", model="qwen2.5-coder:1.5b", use_mock=False, force_offline=False):
        self.base_url = base_url
        self.model = model
        self.use_mock = use_mock
        self.force_offline = force_offline
        self.mock = None
        if use_mock:
            from src.core.ollama_mock import OllamaMock
            self.mock = OllamaMock()

    def check_connection(self):
        """
        Checks if Ollama is reachable.
        """
        if self.use_mock:
            return self.mock.check_connection()
            
        try:
            with urllib.request.urlopen(self.base_url, timeout=5) as response:
                return response.status == 200
        except Exception:
            return False

    def generate_completion(self, prompt, system_prompt=None):
        """
        Generates text completion using the configured model.
        """
        if self.force_offline:
            print("[Ollama] Force Offline Mode: Skipping LLM call.")
            return None

        if self.use_mock:
            return self.mock.generate(prompt, system_prompt)

        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        if system_prompt:
            payload["system"] = system_prompt

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

        try:
            # Added 30s timeout for local LLM generation
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("response", "")
        except Exception as e:
            print(f"[Ollama] Generation failed (timeout/error): {e}")
            return None

    def generate_tool_code(self, tool_name, description):
        """
        Generates Python code for a tool based on description.
        Returns the raw code string (markdown stripped if possible).
        """
        system_prompt = (
            "You are an expert Python tool developer. "
            "Generate a complete, self-contained Python class for the requested tool. "
            "The class must have an 'execute' method. "
            "Output ONLY the Python code. No markdown formatting, no explanations."
            "Do not use external libraries other than standard library."
        )
        
        user_prompt = (
            f"Create a tool named '{tool_name}' that matches this description: {description}. "
            f"Ensure the class is named '{tool_name.replace('_', ' ').title().replace(' ', '')}'."
        )

        code = self.generate_completion(user_prompt, system_prompt)
        
        if code:
            # Basic cleanup of markdown fences if present
            code = code.replace("```python", "").replace("```", "").strip()
            return code
    def apply_rsi_adaptation(self, successful_aha_moments):
        """
        Autopoietic RSI Transformer (NOV-011)
        Simulates the generation of LoRA adapters from successful "AHA" moments.
        """
        count = len(successful_aha_moments)
        print(f"[Ollama] Applying RSI Adaptation for {count} moments.")
        self.adaptation_scalar = min(1.5, 1.0 + (count * 0.05))
        return {"status": "SUCCESS", "new_adaptation": self.adaptation_scalar}
