
import os
import re

def purge_non_ascii(directory):
    print(f"Purging non-ASCII from {directory}...")
    
    # Use hex codes to avoid self-mutilation during cleanup
    replacements = {
        0x03a9: 'Omega',    # Omega
        0x03c4: 'tau',      # tau
        0x03b1: 'alpha',    # alpha
        0x0394: 'delta',    # delta
        0x2b21: '*',        # *
        0x25c8: '+',        # +
        0x25c9: 'o',        # o
        0x25ce: 'O',        # O
        0x2726: '*',        # *
        0x27f3: '@',        # @
        0x2192: '->',       # ->
        0x2264: '<=',       # <=
        0x2265: '>=',       # >=
        0x2026: '...',      # ...
        0x2014: '-',        # -
        0x2500: '-',        # -
        0x2502: '|',        # |
        0x250c: '+',        # +
        0x2510: '+',        # +
        0x2514: '+',        # +
        0x2518: '+',        # +
    }
    
    # Reverse map for emojis and other multi-char symbols
    text_replacements = {
        '[Target]': '[Target]',
        '[Idea]': '[Idea]',
        '[Evolution]': '[Evolution]',
        '[Action]': '[Action]',
        '[Tool]': '[Tool]',
        '[UI]': '[UI]',
        '[Safety]': '[Safety]',
        '[Agent]': '[Agent]',
        '[Pack]': '[Pack]',
        '[Knowledge]': '[Knowledge]',
        '[OK]': '[OK]',
        '[Launch]': '[Launch]'
    }

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.py', '.html', '.css', '.js', '.md')):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    new_content = content
                    # Handle text replacements first
                    for text, rep in text_replacements.items():
                        new_content = new_content.replace(text, rep)
                    
                    # Handle char replacements
                    final_content = []
                    for char in new_content:
                        o = ord(char)
                        if o in replacements:
                            final_content.append(replacements[o])
                        elif o < 128:
                            final_content.append(char)
                        else:
                            # Generic fallback for anything else non-ASCII
                            final_content.append('?')
                    
                    final_str = "".join(final_content)
                    
                    if final_str != content:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(final_str)
                        print(f"Cleaned: {path}")
                except Exception as e:
                    print(f"Error cleaning {path}: {e}")

if __name__ == "__main__":
    base_dir = os.getcwd()
    for d in ['src', 'scripts', 'tests', 'data/logs']:
        target = os.path.join(base_dir, d)
        if os.path.exists(target):
            purge_non_ascii(target)
