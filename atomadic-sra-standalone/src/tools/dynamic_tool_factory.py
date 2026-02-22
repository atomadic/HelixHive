
import os
import ast
import importlib.util
import sys

class DynamicToolFactory:
    """
    Dynamic Tool Factory
    Handles creation, validation, and registration of new tools at runtime.
    """
    def __init__(self, tools_dir="src/tools"):
        self.tools_dir = tools_dir
        os.makedirs(self.tools_dir, exist_ok=True)

    def validate_syntax(self, code_content):
        """
        Validates Python syntax of the provided code.
        Returns (True, None) if valid, (False, error_message) if invalid.
        """
        try:
            ast.parse(code_content)
            return True, None
        except SyntaxError as e:
            return False, f"Syntax Error: {e}"
        except Exception as e:
            return False, f"Validation Error: {e}"

    def create_tool_file(self, tool_name, code_content):
        """
        Writes the tool code to a file in the tools directory.
        Returns the absolute path to the created file.
        """
        valid, error = self.validate_syntax(code_content)
        if not valid:
            raise ValueError(f"Invalid code provided for tool {tool_name}: {error}")

        # Ensure filename is safe
        safe_name = "".join(c for c in tool_name if c.isalnum() or c in ('_',)).lower()
        if not safe_name.endswith("_tool"):
            safe_name += "_tool"
        
        filename = f"{safe_name}.py"
        filepath = os.path.join(self.tools_dir, filename)
        
        # Add tool registration header if missing (simple heuristic)
        if "class " not in code_content:
             # If it's just a function, wrap or checking might be needed, 
             # but assuming agent generates full module for now.
             pass

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code_content)
            
        print(f"[Factory] Created tool file: {filepath}")
        return filepath

    def register_tool(self, filepath):
        """
        Dynamically loads the python file as a module.
        """
        module_name = os.path.basename(filepath).replace(".py", "")
        spec = importlib.util.spec_from_file_location(module_name, filepath)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            print(f"[Factory] Registered module: {module_name}")
            return module
        else:
            raise ImportError(f"Could not load module specification for {filepath}")
