import os
import re
from pathlib import Path

# Define the base directory
BASE_DIR = Path(__file__).parent

# Define the import mappings
IMPORT_MAPPINGS = {
    # Old imports to new imports
    "from vector_database": "from opendiscourse.services.vector_store",
    "import vector_database": "from opendiscourse.services import vector_store",
    "from database": "from opendiscourse.db.database",
    "import database": "from opendiscourse.db import database",
    "from base": "from opendiscourse.db.base",
    "import base": "from opendiscourse.db import base",
    "from models": "from opendiscourse.db.models",
    "import models": "from opendiscourse.db import models",
    "from entity_extractor": "from opendiscourse.entity_extractor",
    "import entity_extractor": "from opendiscourse import entity_extractor",
    "from retry_decorator": "from opendiscourse.utils.decorators",
    "import retry_decorator": "from opendiscourse.utils import decorators",
}


def update_file_imports(file_path):
    """Update imports in a single file."""
    try:
        # Try with utf-8 first, fall back to latin-1 if that fails
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, encoding="latin-1") as f:
                content = f.read()

        original_content = content

        # Update imports
        for old_import, new_import in IMPORT_MAPPINGS.items():
            # Handle 'from x import y' style imports
            content = re.sub(
                rf"^from\s+{re.escape(old_import)}\s+import",
                f"from {new_import} import",
                content,
                flags=re.MULTILINE,
            )
            # Handle 'import x' style imports
            content = re.sub(
                rf"^import\s+{re.escape(old_import)}\b",
                new_import,
                content,
                flags=re.MULTILINE,
            )

        # Only write if changes were made
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Updated imports in {file_path}")
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def should_skip_path(path):
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


def main():
    # Get all Python files in the project, excluding virtual environments and caches
    python_files = []
    for root, _, files in os.walk(BASE_DIR):
        if should_skip_path(root):
            continue
        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)

    # Also include Python files in the root directory
    for file in BASE_DIR.glob("*.py"):
        if file.name != "update_imports.py":  # Skip self
            python_files.append(file)

    # Process each file
    updated_count = 0
    for file_path in python_files:
        if update_file_imports(file_path):
            updated_count += 1

    print(f"\nUpdated imports in {updated_count} files.")


if __name__ == "__main__":
    main()
