import ast
import sys
import re
from pathlib import Path

MIN_LENGTH = 3

CAMEL_CASE_RE = re.compile(r'^[a-z]+(?:[A-Z][a-z0-9]*)+$')
SNAKE_CASE_RE = re.compile(r'^[a-z]+(?:_[a-z0-9]+)*$')


# Check if the file name is snake_case
def check_filename(path):
    filename = Path(path).name
    if not SNAKE_CASE_RE.match(filename.split('.')[0]):
        return False, f"Module name '{filename}' is not in snake_case"
    return True, None

def check_identifier(name):
    if len(name) < MIN_LENGTH:
        return False, "too short (< 3 characters)"
    if name.startswith('__') and name.endswith('__'):
        return True, None  # Dunder methods like __init__
    if name.isupper():
        return True, None  # Constants like MAX_SIZE
    if name.startswith('visit_'):
        return True, None  # AST visitor methods
    if name[0].isupper() and '_' not in name:
        return True, None  # PascalCase (e.g., class names)
    if CAMEL_CASE_RE.match(name) or SNAKE_CASE_RE.match(name):
        return True, None  # Valid snake_case or camelCase
    return False, "not snake_case or camelCase"


class IdentifierVisitor(ast.NodeVisitor):
    def __init__(self):
        self.invalid_identifiers = []

    def report(self, name, node):
        valid, reason = check_identifier(name)
        if not valid:
            self.invalid_identifiers.append((name, node.lineno, reason))

    def visit_FunctionDef(self, node):
        self.report(node.name, node)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.report(node.name, node)
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):  # variable assignment
            self.report(node.id, node)

    def visit_arg(self, node):
        self.report(node.arg, node)


def check_file(path):
    # Check the filename first
    valid, message = check_filename(path)
    if not valid:
        print(f"{path}: {message}")
        return False
    
    try:
        content = Path(path).read_text(encoding='utf-8')
    except Exception as e:
        print(f"{path}: could not read file - {e}")
        return False

    try:
        tree = ast.parse(content, filename=path)
    except SyntaxError as e:
        print(f"{path}: syntax error - {e}")
        return False

    visitor = IdentifierVisitor()
    visitor.visit(tree)

    for name, lineno, reason in visitor.invalid_identifiers:
        print(f"{path}:{lineno} - Invalid identifier '{name}': {reason}")

    return len(visitor.invalid_identifiers) == 0


def main():
    failed = False
    for path in sys.argv[1:]:
        if not check_file(path):
            failed = True
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
