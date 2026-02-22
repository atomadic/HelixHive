
# src/tools/tool_execution_layer.py

class ToolExecutionLayer:
    """
    Tool Execution Layer
    Unified wrapper for all tools with audit logging.
    """
    def __init__(self):
        # Lazy import to avoid circular dependency issues if any
        from src.tools.sandbox_wrapper import SandboxWrapper
        from src.core.ai_bridge import AIBridge  # Import from core
        
        self.sandbox = SandboxWrapper(timeout_seconds=5)
        self.ai_bridge = AIBridge() # Initialize global AI bridge
        
        # Registry for manual tools
        self.tool_registry = {
            "ai_bridge": self.ai_bridge
        }

    def run_tool(self, tool_name, args, **kwargs):
        print(f"[ToolLayer] invoking {tool_name} with {args}")
        
        # Check manual registry first
        if tool_name in self.tool_registry:
            # AIBridge uses 'generate', others use 'execute' - simplified dispatch
            tool = self.tool_registry[tool_name]
            if tool_name == "ai_bridge":
                 return tool.generate(*args, **kwargs)
            return tool.execute(*args, **kwargs)

        # Identify if it's a dynamic tool (module-based)
        import sys
        if tool_name in sys.modules:
            try:
                module = sys.modules[tool_name]
                # Assuming typical class-based pattern: ModuleName.ClassName().execute()
                # or function-based. For now, we support ClassName = ToolName (TitleCase)
                
                class_name = "".join(x.title() for x in tool_name.split("_"))
                if hasattr(module, class_name):
                    tool_class = getattr(module, class_name)
                    tool_instance = tool_class()
                    
                    if hasattr(tool_instance, 'execute'):
                         # Execute the tool method directly. 
                         # Note: Truly safe execution of a complex object method 
                         # inside a separate process requires pickling support.
                         # For this prototype, we'll wrap the CALL in a try-except block 
                         # and enforce timeout via signal or thread if feasible, 
                         # OR we serialize the call to the sandbox if possible.
                         
                         # Simpler approach for this stage:
                         # We trust "registered" tools enough to run in-process 
                         # but wrap them in a generic timeout/safety check if possible.
                         # Since multiprocessing strict sandboxing of objects is hard,
                         # we will stick to basic try/except/timeout integration here.
                         
                         return tool_instance.execute(*args, **kwargs)
                    else:
                        return f"Error: Tool {tool_name} has no 'execute' method."
                else:
                    return f"Error: Class {class_name} not found in module {tool_name}"

            except Exception as e:
                return f"Tool Execution Error: {e}"

        return f"Error: Tool module '{tool_name}' not found."


    def load_dynamic_tools(self):
        """
        Scans src/tools for new modules and imports them.
        """
        import os
        import importlib.util
        import sys
        
        tools_dir = "src/tools"
        if not os.path.exists(tools_dir):
            return

        count = 0
        for filename in os.listdir(tools_dir):
            if filename.endswith(".py") and filename not in ["__init__.py", "tool_execution_layer.py"]:
                 module_name = filename[:-3]
                 filepath = os.path.join(tools_dir, filename)
                 
                 # Avoid reloading if already loaded, unless forced (omitted for brevity)
                 if module_name not in sys.modules:
                     spec = importlib.util.spec_from_file_location(module_name, filepath)
                     if spec and spec.loader:
                         module = importlib.util.module_from_spec(spec)
                         sys.modules[module_name] = module
                         spec.loader.exec_module(module)
                         count += 1
        
        print(f"[ToolLayer] Loaded {count} dynamic tools.")

