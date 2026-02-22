
import json
import random
import time

class OllamaMock:
    """
    Ollama Mock Provider (NOV-002)
    Provides deterministic, high-quality responses for system testing.
    Simulates LLM reasoning and code generation.
    """
    def __init__(self, latency_range=(0.1, 0.5)):
        self.latency_range = latency_range

    def generate(self, prompt, system_prompt=None):
        """Simulate a completion response."""
        # Add artificial latency to simulate temporal weight
        delay = random.uniform(*self.latency_range)
        time.sleep(delay)
        
        prompt_lower = prompt.lower()
        
        # 1. Handle Tool Generation
        if "create a tool named" in prompt_lower:
            tool_name = prompt.split("named '")[1].split("'")[0] if "'" in prompt else "unknown_tool"
            class_name = "".join(x.title() for x in tool_name.split("_"))
            return f"""
class {class_name}:
    \"\"\"
    Mock-generated tool: {tool_name}
    \"\"\"
    def execute(self, *args, **kwargs):
        return f"Mock {tool_name} executed with args: {{args}}"
"""

        # 2. Handle Governance/Debate
        if "debate" in prompt_lower or "propose" in prompt_lower:
            return "I propose that we prioritize grounding over speed. My reasoning follows the E8 lattice constraints."

        # 3. Handle General Reasoning
        return "Based on my internal reasoning substrate, the optimal path is to continue the recursive audit loop."

    def check_connection(self):
        """Always return True for the mock."""
        return True
