
import multiprocessing
import time
import builtins

def _unsafe_exec_wrapper(code, restricted_globals, result_queue):
    """
    Worker function to execute code in a separate process.
    """
    try:
        exec(code, restricted_globals)
        # Attempt to capture result if 'result' variable is set, otherwise None
        result_queue.put(restricted_globals.get('result', None))
    except Exception as e:
        result_queue.put(e)

class SandboxWrapper:
    """
    Sandbox Wrapper
    Provides a somewhat isolated execution environment for dynamic code.
    Not a perfect security boundary, but prevents accidental infinite loops/damage.
    """
    def __init__(self, timeout_seconds=5):
        self.timeout_seconds = timeout_seconds
        
        # Define allowed builtins
        self.safe_builtins = {
            'abs': abs, 'all': all, 'any': any, 'ascii': ascii, 'bin': bin, 
            'bool': bool, 'bytearray': bytearray, 'bytes': bytes, 'chr': chr, 
            'dict': dict, 'divmod': divmod, 'enumerate': enumerate, 'filter': filter, 
            'float': float, 'format': format, 'frozenset': frozenset, 'getattr': getattr, 
            'hasattr': hasattr, 'hash': hash, 'hex': hex, 'id': id, 'int': int, 
            'isinstance': isinstance, 'issubclass': issubclass, 'iter': iter, 
            'len': len, 'list': list, 'map': map, 'max': max, 'min': min, 
            'next': next, 'object': object, 'oct': oct, 'ord': ord, 'pow': pow, 
            'print': print, 'range': range, 'repr': repr, 'reversed': reversed, 
            'round': round, 'set': set, 'slice': slice, 'sorted': sorted, 
            'str': str, 'sum': sum, 'super': super, 'tuple': tuple, 'type': type, 
            'zip': zip, 'Exception': Exception, 'ValueError': ValueError
        }

    def execute(self, code, context={}):
        """
        Executes code string with restricted globals in a separate process with timeout.
        """
        restricted_globals = {'__builtins__': self.safe_builtins}
        restricted_globals.update(context)
        
        queue = multiprocessing.Queue()
        process = multiprocessing.Process(target=_unsafe_exec_wrapper, args=(code, restricted_globals, queue))
        process.start()
        
        process.join(self.timeout_seconds)
        
        if process.is_alive():
            process.terminate()
            process.join()
            raise TimeoutError(f"Execution timed out after {self.timeout_seconds} seconds.")
            
        if not queue.empty():
            result = queue.get()
            if isinstance(result, Exception):
                raise result
            return result
        return None
