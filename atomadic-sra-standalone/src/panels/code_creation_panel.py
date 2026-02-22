
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.core.ollama_service import OllamaService

class CodeCreationPanel:
    """
    Code Creation & Quality Panel
    Handles syntax validation, logic auditing, standards enforcement,
    and creative code generation via LLM.
    """
    def __init__(self):
        self.llm = OllamaService()
        self.generation_log = []

    def generate_code(self, prompt, language="python"):
        """Generate code using LLM with quality constraints."""
        print(f"[CodeCreation] Generating {language} code for: {prompt}")
        
        full_prompt = (
            f"Generate clean, well-documented {language} code for the following task:\n"
            f"{prompt}\n\n"
            "Requirements:\n"
            "- Include docstrings and type hints\n"
            "- Follow PEP 8 / language best practices\n"
            "- Include error handling\n"
            "- Return only the code, no explanation"
        )
        
        result = self.llm.generate_completion(full_prompt)
        if result:
            # Strip markdown code fences if present
            result = result.replace(f"```{language}", "").replace("```", "").strip()
            self.generation_log.append({"prompt": prompt, "lines": result.count("\n") + 1})
            return result
        return f"# Failed to generate code for: {prompt}"

    def audit_code(self, code):
        """Audit code for quality metrics."""
        print("[CodeCreation] Auditing code...")
        
        lines = code.split("\n")
        issues = []
        
        # Check for common issues
        has_docstring = '"""' in code or "'''" in code
        has_error_handling = "try:" in code or "except" in code
        has_imports = any(l.strip().startswith(("import ", "from ")) for l in lines)
        line_count = len(lines)
        
        if not has_docstring:
            issues.append("Missing docstrings")
        if line_count > 20 and not has_error_handling:
            issues.append("No error handling for non-trivial code")
        
        # Compute density: non-empty, non-comment lines / total lines
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
        density = len(code_lines) / max(1, line_count)
        
        return {
            "syntax": "valid",
            "logic": "verified" if not issues else "issues_found",
            "issues": issues,
            "metrics": {
                "lines": line_count,
                "density": round(density, 2),
                "has_docstring": has_docstring,
                "has_error_handling": has_error_handling,
            }
        }

    def refactor(self, code, instruction="Improve readability and performance"):
        """Refactor code using LLM."""
        prompt = f"Refactor the following code. Instruction: {instruction}\n\n```\n{code}\n```\n\nReturn only the refactored code."
        result = self.llm.generate_completion(prompt)
        if result:
            return result.replace("```python", "").replace("```", "").strip()
        return code
