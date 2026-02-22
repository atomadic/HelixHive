
import subprocess
import time
import os

class ShellTool:
    """
    Shell Tool
    Secure shell execution with permission gating and audit logging.
    """
    BLOCKED_COMMANDS = ["rm -rf", "format", "del /s", "rmdir /s", "shutdown", "reboot"]

    def __init__(self):
        self.execution_log = []
        self.permissions = {"shell_enabled": True, "max_timeout": 30}

    def execute(self, command, timeout=None, cwd=None):
        """Execute a shell command with safety checks."""
        timeout = timeout or self.permissions["max_timeout"]
        
        # Permission gate
        if not self.permissions["shell_enabled"]:
            return {"status": "BLOCKED", "reason": "Shell execution disabled"}
        
        # Safety check
        if self._is_dangerous(command):
            result = {"status": "BLOCKED", "reason": f"Dangerous command detected: {command}"}
            self._log(command, result)
            return result
        
        print(f"[Shell] Executing: {command}")
        
        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd
            )
            
            result = {
                "status": "SUCCESS" if proc.returncode == 0 else "ERROR",
                "exit_code": proc.returncode,
                "stdout": proc.stdout[:2000] if proc.stdout else "",
                "stderr": proc.stderr[:2000] if proc.stderr else "",
            }
        except subprocess.TimeoutExpired:
            result = {"status": "TIMEOUT", "reason": f"Command exceeded {timeout}s"}
        except Exception as e:
            result = {"status": "ERROR", "reason": str(e)}
        
        self._log(command, result)
        return result

    def _is_dangerous(self, command):
        """Check if command matches blocked patterns."""
        cmd_lower = command.lower()
        return any(blocked in cmd_lower for blocked in self.BLOCKED_COMMANDS)

    def _log(self, command, result):
        """Audit log entry."""
        self.execution_log.append({
            "command": command,
            "result": result["status"],
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        })

    def get_log(self):
        return self.execution_log

class InteractiveShell(ShellTool):
    """
    Interactive Shell
    Maintains a persistent subprocess.Popen session for stateful interactions.
    """
    def __init__(self):
        super().__init__()
        self.process = None
        self.output_queue = []

    def start_session(self, cwd=None):
        """Start a persistent shell session."""
        if self.process:
            return "Session already active."
        
        print("[Shell] Starting interactive session...")
        self.process = subprocess.Popen(
            "cmd.exe" if os.name == "nt" else "/bin/bash",
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True,
            cwd=cwd,
            bufsize=1
        )
        return "Session started."

    def send_input(self, input_str):
        """Send input to the active session."""
        if not self.process:
            return "Error: No active session."
        
        if self._is_dangerous(input_str):
             return "Error: Dangerous command blocked."
             
        try:
            self.process.stdin.write(input_str + "\n")
            self.process.stdin.flush()
            return "Input sent."
        except Exception as e:
            return f"Error sending input: {e}"

    def read_output(self, timeout=1):
        """Read current stdout/stderr from the session."""
        if not self.process:
            return "Error: No active session."
        
        # This is a basic non-blocking read for a prototype
        # Re-implementation would use threads to continuously drain stdout
        return "Not fully implemented: Output streaming requires background threading."

    def close_session(self):
        """Terminate the persistent session."""
        if self.process:
            self.process.terminate()
            self.process = None
            return "Session closed."
        return "No session to close."
