import ast
import os
import re

def parse_audit_report(report_path):
    issues = []
    current_file = None
    with open(report_path, "r", encoding="utf-8") as f:
        for line in f:
            file_match = re.match(r"## File: (.*\.py)", line)
            if file_match:
                current_file = file_match.group(1)
            name_match = re.match(r"- \*\*Name:\*\* `(.*?)`", line)
            if name_match and current_file:
                issues.append({"filepath": current_file, "name": name_match.group(1)})
    return issues

class DefinitionLocator(ast.NodeVisitor):
    def __init__(self, target_name):
        self.target_name = target_name
        self.definition_info = None  # (start_lineno, end_lineno)

    def visit_FunctionDef(self, node):
        if node.name == self.target_name:
            self._set_definition_info(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        if node.name == self.target_name:
            self._set_definition_info(node)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        if node.name == self.target_name:
            self._set_definition_info(node)
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            if name == self.target_name:
                self._set_definition_info(node)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            if name == self.target_name:
                self._set_definition_info(node)
        self.generic_visit(node)

    def visit_Assign(self, node):
        # For simple variable assignments
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == self.target_name:
                self._set_definition_info(node)
        self.generic_visit(node)

    def _set_definition_info(self, node):
        # Determine the start line, accounting for decorators
        start_lineno = node.lineno
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.decorator_list:
            # Decorators are before the def/class line, find the earliest decorator's line
            start_lineno = min(start_lineno, min(d.lineno for d in node.decorator_list))

        # Determine the end line, which is usually the last line of the node
        end_lineno = getattr(node, 'end_lineno', node.lineno) # Fallback if end_lineno not available
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # For functions/classes, body can extend to many lines
            if node.body:
                end_lineno = max(end_lineno, getattr(node.body[-1], 'end_lineno', node.body[-1].lineno))
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            # Imports are usually single line, but ensure end_lineno is present
            pass
        elif isinstance(node, ast.Assign):
            # Assignments can also be multi-line for complex values, but for simple ones, end_lineno is usually accurate
            pass

        self.definition_info = (start_lineno, end_lineno)

def get_code_block_to_remove(filepath, name):
    with open(filepath, "r", encoding="utf-8") as f:
        content_lines = f.readlines()

    try:
        tree = ast.parse("".join(content_lines))
        locator = DefinitionLocator(name)
        locator.visit(tree)

        if locator.definition_info:
            start_line, end_line = locator.definition_info
            # Extract the lines, preserving original line endings for apply_diff
            # Adjust for 0-based list indexing vs 1-based line numbers
            old_string_lines = content_lines[start_line - 1:end_line]
            old_string = "".join(old_string_lines)
            return old_string, start_line, end_line
        return None, None, None
    except SyntaxError as e:
        print(f"Syntax error in {filepath}: {e}")
        return None, None, None

def main():
    report_path = "atomadic-sra-standalone/audit_report.md"
    issues = parse_audit_report(report_path)

    repairs_made = []
    failed_repairs = []

    # Group issues by filepath to minimize file read/write operations
    issues_by_filepath = {}
    for issue in issues:
        filepath = issue["filepath"]
        if filepath not in issues_by_filepath:
            issues_by_filepath[filepath] = []
        issues_by_filepath[filepath].append(issue["name"])

    for filepath, names_to_remove in issues_by_filepath.items():
        if not os.path.exists(filepath):
            for name in names_to_remove:
                failed_repairs.append(f"File not found: {filepath} for {name}")
            continue

        # Read the file content once for all removals in this file
        with open(filepath, "r", encoding="utf-8") as f:
            original_content = f.read()

        # Prepare diffs for this file
        diff_blocks = []
        current_file_lines = original_content.splitlines(keepends=True)

        # Iterate in reverse order of line number to avoid issues with line numbers shifting
        names_to_remove_with_lines = []
        for name in names_to_remove:
            old_string, start_line, end_line = get_code_block_to_remove(filepath, name)
            if old_string:
                names_to_remove_with_lines.append((name, old_string, start_line, end_line))
            else:
                failed_repairs.append(f"Could not locate precise definition for `{name}` in {filepath}")

        # Sort in reverse order of start_line to apply diffs from bottom up
        names_to_remove_with_lines.sort(key=lambda x: x[2], reverse=True)

        for name, old_string, start_line, end_line in names_to_remove_with_lines:
            # Construct the diff string
            diff_string = (f"<<<<<<< SEARCH\n:start_line:{start_line}\n-------\n{old_string}=======\n\n>>>>>>> REPLACE")
            
            try:
                print(f"Applying diff for `{name}` in {filepath} (lines {start_line}-{end_line})")
                # Use the actual apply_diff tool
                default_api.apply_diff(path=filepath, diff=diff_string)
                repairs_made.append(f"Removed `{name}` from {filepath} (lines {start_line}-{end_line})")
            except Exception as e:
                failed_repairs.append(f"Error applying diff for `{name}` in {filepath}: {e}")

    print("\n--- Repair Summary ---")
    if repairs_made:
        for repair in repairs_made:
            print(f"SUCCESS: {repair}")
    else:
        print("No repairs were successfully made.")

    if failed_repairs:
        print("\n--- Failed Repairs ---")
        for failed in failed_repairs:
            print(f"FAILED: {failed}")

if __name__ == "__main__":
    main()
