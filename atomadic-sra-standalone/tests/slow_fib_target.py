
import time

def slow_fib(n):
    if n <= 1:
        return n
    # Inefficient recursive implementation
    return slow_fib(n-1) + slow_fib(n-2)

if __name__ == "__main__":
    start = time.time()
    # 30 is large enough to be slowish (~0.3s) but not freeze testing
    print(f"Fib(30) = {slow_fib(30)}")
    print(f"Time taken: {time.time() - start:.4f}s")
