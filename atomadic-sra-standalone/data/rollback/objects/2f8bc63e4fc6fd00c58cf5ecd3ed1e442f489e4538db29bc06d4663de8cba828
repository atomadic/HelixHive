
import os
from src.agents.luminary_base import LuminaryBase
from src.core.ollama_service import OllamaService
from src.tools.profiler_tool import ProfilerTool

class OptimizationAgent(LuminaryBase):
    """
    Optimization Agent
    Analyzes code performance and rewrites it for efficiency using LLM.
    """
    def __init__(self, name="OptimizationAgent"):
        super().__init__(name)
        self.profiler = ProfilerTool()
        self.llm = OllamaService()
        print(f"[{self.name}] Optimizer initialized.")

    def optimize_file(self, target_file):
        """
        Profiles the file, sends analysis to LLM, and generates an optimized version.
        """
        print(f"[{self.name}] Analyzing {target_file}...")
        
        # 1. Profile
        profile_report = self.profiler.execute(target_file)
        if "Error" in profile_report and "Profiling Failed" not in profile_report:
             return {"status": "error", "message": profile_report}
        
        print(f"[{self.name}] Profile collected. Identifying bottlenecks...")
        
        # 2. Read Source
        with open(target_file, "r") as f:
            source_code = f.read()

        # 3. Request Optimization
        system_prompt = (
            "You are a Senior Python Performance Engineer. "
            "Analyze the provided code and profile report. "
            "Rewrite the code to be significantly more efficient (faster or less memory). "
            "Keep the same functionality and inputs/outputs. "
            "Output ONLY the optimized Python code."
        )
        
        user_prompt = (
            f"SOURCE CODE:\n```python\n{source_code}\n```\n\n"
            f"PROFILE REPORT:\n{profile_report}\n\n"
            "Optimize this code. Use better algorithms or data structures if possible."
        )

        print(f"[{self.name}] Consulting Ollama for optimization...")
        optimized_code = self.llm.generate_completion(user_prompt, system_prompt)
        
        if not optimized_code:
            return {"status": "error", "message": "LLM failed to generate optimization."}

        # Cleanup markdown
        optimized_code = optimized_code.replace("```python", "").replace("```", "").strip()
        
        # 4. Save Optimized Version
        directory, filename = os.path.split(target_file)
        name_root, ext = os.path.splitext(filename)
        optimized_filename = f"{name_root}_optimized{ext}"
        optimized_path = os.path.join(directory, optimized_filename)
        
        with open(optimized_path, "w") as f:
            f.write(optimized_code)
            
        print(f"[{self.name}] Optimization complete. Saved to {optimized_path}")
        return {
            "status": "success", 
            "original": target_file, 
            "optimized": optimized_path,
            "profile_summary": profile_report[:200] + "..." # Truncate for log
        }
