
import ast
import os

def get_module_name(filepath, root_dir):
    """Compute module name from file path relative to root_dir."""
    relpath = os.path.relpath(filepath, root_dir)
    # Remove .py extension and replace path separators with dots
    module_name = relpath.replace(os.sep, '.')
    if module_name.endswith('.py'):
        module_name = module_name[:-3]
    return module_name

class EnhancedCodeFinder(ast.NodeVisitor):
    """Collects definitions, import bindings, and usages within a file, with depth awareness."""
    def __init__(self, filepath, module_name):
        self.filepath = filepath
        self.module_name = module_name
        self.definitions = {}  # name -> (type, start_line, end_line)
        self.import_bindings = {}  # local_name -> (source_module, imported_name)
        self.local_usages = set()  # names loaded (including attribute bases)
        self.attribute_usages = set()  # (base_name, attr)
        self.depth = 0

    def visit_FunctionDef(self, node):
        if self.depth == 0:
            self.definitions[node.name] = ('function', node.lineno, getattr(node, 'end_lineno', node.lineno))
        self.depth += 1
        self.generic_visit(node)
        self.depth -= 1

    def visit_AsyncFunctionDef(self, node):
        if self.depth == 0:
            self.definitions[node.name] = ('function', node.lineno, getattr(node, 'end_lineno', node.lineno))
        self.depth += 1
        self.generic_visit(node)
        self.depth -= 1

    def visit_ClassDef(self, node):
        if self.depth == 0:
            self.definitions[node.name] = ('class', node.lineno, getattr(node, 'end_lineno', node.lineno))
        self.depth += 1
        self.generic_visit(node)
        self.depth -= 1

    def visit_Import(self, node):
        if self.depth == 0:
            for alias in node.names:
                full_name = alias.name
                local_name = alias.asname if alias.asname else full_name.split('.')[0]
                self.import_bindings[local_name] = (full_name, None)
                self.definitions[local_name] = ('import', node.lineno, getattr(node, 'end_lineno', node.lineno))
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if self.depth == 0:
            level = node.level
            if level == 0:
                source_mod = node.module if node.module else ''
            else:
                # Relative import: resolve relative to current module
                parts = self.module_name.split('.')
                if level > len(parts):
                    # Cannot resolve; skip
                    source_mod = None
                else:
                    base_parts = parts[:-level]
                    if node.module:
                        source_mod = '.'.join(base_parts + [node.module]) if base_parts or node.module else node.module
                    else:
                        source_mod = '.'.join(base_parts) if base_parts else ''
            if source_mod is not None:
                for alias in node.names:
                    if alias.name == '*':
                        # Star imports are not tracked for simplicity
                        continue
                    local_name = alias.asname if alias.asname else alias.name
                    self.import_bindings[local_name] = (source_mod, alias.name)
                    self.definitions[local_name] = ('import', node.lineno, getattr(node, 'end_lineno', node.lineno))
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.local_usages.add(node.id)
        elif isinstance(node.ctx, ast.Store) and self.depth == 0:
            # Top-level variable assignment (not function/class, which are handled separately)
            # Avoid double-counting if it's also a function/class? Those don't appear as Store Name nodes.
            self.definitions[node.id] = ('variable', node.lineno, getattr(node, 'end_lineno', node.lineno))
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name):
            base_name = node.value.id
            attr = node.attr
            self.attribute_usages.add((base_name, attr))
        self.generic_visit(node)

def audit_file_enhanced(filepath, root_dir):
    """Parse a file and return its module data."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    try:
        tree = ast.parse(content)
        module_name = get_module_name(filepath, root_dir)
        finder = EnhancedCodeFinder(filepath, module_name)
        finder.visit(tree)
        return {
            'module_name': module_name,
            'definitions': finder.definitions,
            'import_bindings': finder.import_bindings,
            'local_usages': finder.local_usages,
            'attribute_usages': finder.attribute_usages,
            'filepath': filepath
        }
    except SyntaxError as e:
        return {
            'filepath': filepath,
            'error': str(e)
        }

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    output_file = os.path.join(root_dir, "audit_report.md")

    # Collect all Python files from the project, excluding non-code directories
    exclude_dirs = {'data', 'docs', 'notebooks', '__pycache__', 'static', 'assets', 'node_modules', '.git'}
    all_files = []
    for root, dirs, files in os.walk(root_dir):
        # Modify dirs in-place to skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file).replace("\\", "/")
                all_files.append(filepath)

    # First pass: collect data from all files
    all_modules = {}  # module_name -> data
    for filepath in all_files:
        print(f"Analyzing {filepath}...")
        data = audit_file_enhanced(filepath, root_dir)
        if 'error' in data:
            print(f"  Syntax error in {filepath}: {data['error']}")
            continue
        module_name = data['module_name']
        all_modules[module_name] = data

    # Build cross-reference: which symbols are used externally via imports
    externally_used = set()  # (source_module, symbol_name)

    for module_name, data in all_modules.items():
        import_bindings = data['import_bindings']
        local_usages = data['local_usages']
        attribute_usages = data['attribute_usages']

        for local_name, (source_mod, imported_name) in import_bindings.items():
            if source_mod is None:
                continue  # Unresolved relative import
            if imported_name is not None:
                # from-import of a specific symbol
                if local_name in local_usages:
                    externally_used.add((source_mod, imported_name))
            else:
                # plain import of a module
                # Check if any attribute of that module is accessed
                for base, attr in attribute_usages:
                    if base == local_name:
                        externally_used.add((source_mod, attr))

    # Second pass: determine unused definitions per file
    all_unused_findings = []

    for module_name, data in all_modules.items():
        definitions = data['definitions']
        local_usages = data['local_usages']
        filepath = data['filepath']

        for name, (def_type, start_line, end_line) in definitions.items():
            # Skip magic methods and single underscore
            if name.startswith("__") and name.endswith("__"):
                continue
            if name in ["_"]:
                continue

            # Check if used locally
            if name in local_usages:
                continue

            # Check if used externally (imported by another module)
            if (module_name, name) in externally_used:
                continue

            # Unused
            all_unused_findings.append({
                "filepath": filepath,
                "type": def_type,
                "name": name,
                "description": f"Unused definition: {name}",
                "start_line": start_line,
                "end_line": end_line
            })

    # Write findings to a markdown report
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Code Audit Report (Enhanced Cross-File Analysis)\n\n")
        if all_unused_findings:
            for finding in all_unused_findings:
                f.write(f"## File: {finding['filepath']}\n")
                f.write(f"- **Type:** {finding['type']}\n")
                f.write(f"- **Name:** `{finding['name']}`\n")
                f.write(f"- **Description:** {finding['description']}\n")
                f.write(f"- **Lines:** {finding['start_line']}-{finding['end_line']}\n\n")
        else:
            f.write("No unused variables, functions, or imports found.\n")
    print(f"Enhanced audit complete. Report saved to {output_file}")

if __name__ == "__main__":
    main()
