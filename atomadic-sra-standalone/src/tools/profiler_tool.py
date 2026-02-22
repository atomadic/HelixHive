
import cProfile
import pstats
import io
import os
import sys

class ProfilerTool:
    """
    Profiler Tool
    Runs a Python script or function under cProfile and returns analysis.
    """
    def execute(self, target_file, sort_by="cumulative", top_n=10):
        """
        Profiles the target python file.
        """
        if not os.path.exists(target_file):
            return f"Error: File {target_file} not found."

        # Create a runner script to execute the target file
        # This approach ensures the target runs in a relatively clean context
        # but captures the profile.
        
        pr = cProfile.Profile()
        pr.enable()
        
        try:
            # We use exec here. Sandbox warning applies, but this is an Admin tool.
            with open(target_file, "r") as f:
                code = compile(f.read(), target_file, 'exec')
                
            # Define a limited global scope or pass current 
            # We'll use a new dict to simulate script execution
            exec_globals = {"__name__": "__main__", "__file__": target_file}
            exec(code, exec_globals)
        except Exception as e:
            pr.disable()
            return f"Profiling Failed during execution: {e}"
            
        pr.disable()
        
        # Capture stats
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats(sort_by)
        ps.print_stats(top_n)
        
        return s.getvalue()
