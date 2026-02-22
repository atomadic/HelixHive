
import os
import sys

def check_ascii(directory):
    print(f"Checking {directory} for non-ASCII characters...")
    non_ascii_found = False
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.py', '.html', '.css', '.js', '.md')):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for i, char in enumerate(content):
                            if ord(char) > 127:
                                print(f"Non-ASCII found in {path} at char {i}: '{char}' (ord={ord(char)})")
                                non_ascii_found = True
                except Exception as e:
                    print(f"Error reading {path}: {e}")
    
    if not non_ascii_found:
        print("Success: No non-ASCII characters found.")
    return non_ascii_found

if __name__ == "__main__":
    src_dir = os.path.join(os.getcwd(), 'src')
    scripts_dir = os.path.join(os.getcwd(), 'scripts')
    found = check_ascii(src_dir)
    found = check_ascii(scripts_dir) or found
    
    if found:
        sys.exit(1)
    else:
        sys.exit(0)
