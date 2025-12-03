import ast
import os
from pathlib import Path

# Define the base directory
BASE_DIR = Path(__file__).parent

# Define the expected import structure
EXPECTED_IMPORTS = {
    "opendiscourse.api",
    "opendiscourse.core",
    "opendiscourse.db",
    "opendiscourse.services",
    "opendiscourse.utils",
}


def should_skip_path(path: Path) -> bool:
    """Check if the path should be skipped."""
    skip_dirs = {
        "venv",
        ".venv",
        "__pycache__",
        ".git",
        ".github",
        ".mypy_cache",
        ".pytest_cache",
    }
    path_str = str(path)
    return any(skip_dir in path_str.split(os.sep) for skip_dir in skip_dirs)


def get_imports(file_path: Path) -> set[str]:
    """Extract all imports from a Python file."""
    with open(file_path, encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            return set()

    imports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                imports.add(name.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])

    return imports


def check_imports() -> tuple[dict[str, list[str]], set[str]]:
    """Check imports in all Python files."""
    # Get all Python files in the project
    python_files = []
    for root, _, files in os.walk(BASE_DIR):
        root_path = Path(root)
        if should_skip_path(root_path):
            continue
        for file in files:
            if file.endswith(".py"):
                python_files.append(root_path / file)

    # Also include Python files in the root directory
    for file in BASE_DIR.glob("*.py"):
        if file.name not in {"update_imports.py", "check_imports.py"}:
            python_files.append(file)

    # Check imports in each file
    invalid_imports = {}
    all_imports = set()

    for file_path in python_files:
        imports = get_imports(file_path)
        all_imports.update(imports)

        # Check for invalid imports
        invalid = [
            imp
            for imp in imports
            if any(imp.startswith(mod) for mod in EXPECTED_IMPORTS)
            and imp not in EXPECTED_IMPORTS
        ]

        if invalid:
            invalid_imports[str(file_path)] = invalid

    return invalid_imports, all_imports


def main():
    print("Checking imports...")
    invalid_imports, all_imports = check_imports()

    if invalid_imports:
        print("\nFound files with potentially incorrect imports:")
        for file_path, imports in invalid_imports.items():
            print(f"\n{file_path}:")
            for imp in imports:
                print(f"  - {imp}")
    else:
        print("\nAll imports look good!")

    print("\nAll unique imports found:")
    for imp in sorted(all_imports):
        print(f"- {imp}")


if __name__ == "__main__":
    main()
