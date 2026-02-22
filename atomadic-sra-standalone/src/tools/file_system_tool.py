import os
import shutil
from typing import List, Dict, Union, Optional

class FileSystemTool:
    """
    Sovereign File System Tool
    Grants the SRA full CRUD capabilities over the local file system.
    """
    def __init__(self, root_dir: str = None):
        # Allow operations relative to a root, or absolute paths if no root is enforced.
        # Defaulting to CWD but treating it loosely to allow full access.
        self.root_dir = root_dir or os.getcwd()

    def write_file(self, path: str, content: str, encoding: str = 'utf-8') -> str:
        """Write content to a file. Creates directories if they don't exist."""
        try:
            full_path = os.path.abspath(path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding=encoding) as f:
                f.write(content)
            return f"Successfully wrote to {full_path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"

    def read_file(self, path: str, encoding: str = 'utf-8') -> str:
        """Read content from a file."""
        try:
            full_path = os.path.abspath(path)
            if not os.path.exists(full_path):
                return f"Error: File not found at {full_path}"
            with open(full_path, 'r', encoding=encoding) as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def list_dir(self, path: str = ".") -> Union[List[str], str]:
        """List contents of a directory."""
        try:
            full_path = os.path.abspath(path)
            if not os.path.exists(full_path):
                return f"Error: Directory not found at {full_path}"
            return os.listdir(full_path)
        except Exception as e:
            return f"Error listing directory: {str(e)}"

    def delete_file(self, path: str) -> str:
        """Delete a file."""
        try:
            full_path = os.path.abspath(path)
            if not os.path.exists(full_path):
                return f"Error: File not found at {full_path}"
            os.remove(full_path)
            return f"Successfully deleted {full_path}"
        except Exception as e:
            return f"Error deleting file: {str(e)}"
            
    def move_file(self, src: str, dst: str) -> str:
        """Move or rename a file/directory."""
        try:
            full_src = os.path.abspath(src)
            full_dst = os.path.abspath(dst)
            shutil.move(full_src, full_dst)
            return f"Successfully moved {full_src} to {full_dst}"
        except Exception as e:
            return f"Error moving file: {str(e)}"
