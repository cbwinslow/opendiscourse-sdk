"""
Validation script for OpenDiscourse SDK.

This script validates that the SDK structure is correct and all components
can be imported. It doesn't require external dependencies beyond Python stdlib.

Author: OpenDiscourse Team
License: MIT
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def validate_structure():
    """Validate that all required files and directories exist."""
    print("Validating SDK structure...")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    required_files = [
        "__init__.py",
        "base.py",
        "exceptions.py",
        "enums.py",
        "examples.py",
        "README.md",
        "setup.py",
        "pyproject.toml",
        "MANIFEST.in",
    ]

    required_dirs = [
        "models",
        "congress",
        "govinfo",
        "openstates",
        "tests",
    ]

    all_good = True

    # Check files
    for filename in required_files:
        filepath = os.path.join(base_dir, filename)
        if os.path.exists(filepath):
            print(f"  ✓ {filename}")
        else:
            print(f"  ✗ {filename} - MISSING")
            all_good = False

    # Check directories
    for dirname in required_dirs:
        dirpath = os.path.join(base_dir, dirname)
        if os.path.isdir(dirpath):
            print(f"  ✓ {dirname}/")
        else:
            print(f"  ✗ {dirname}/ - MISSING")
            all_good = False

    return all_good


def validate_imports():
    """Validate that key components can be imported."""
    print("\nValidating imports...")

    all_good = True

    # Test enum imports (doesn't require pydantic)
    try:
        from opendiscourse_sdk.enums import (
            BillType,
            Chamber,
            StateCode,
        )
        print("  ✓ Enumerations")

        # Verify enum values
        assert BillType.HOUSE_BILL.value == "hr"
        assert Chamber.HOUSE.value == "house"
        assert StateCode.CALIFORNIA.value == "ca"
        print("  ✓ Enum values correct")
    except Exception as e:
        print(f"  ✗ Enumerations - {e}")
        all_good = False

    # Test exception imports
    try:
        from opendiscourse_sdk.exceptions import (
            APIError,
            AuthenticationError,
            OpenDiscourseSDKError,
        )
        print("  ✓ Exceptions")

        # Test exception hierarchy
        assert issubclass(APIError, OpenDiscourseSDKError)
        assert issubclass(AuthenticationError, APIError)
        print("  ✓ Exception hierarchy correct")
    except Exception as e:
        print(f"  ✗ Exceptions - {e}")
        all_good = False

    # Test base client (requires requests, so may fail)
    try:
        from opendiscourse_sdk.base import BaseClient
        print("  ✓ Base client")
    except ImportError as e:
        print(f"  ⚠ Base client - {e} (dependencies not installed)")
    except Exception as e:
        print(f"  ✗ Base client - {e}")
        all_good = False

    # Test main package imports
    try:
        import opendiscourse_sdk
        print("  ✓ Main package")
        print(f"  ✓ Version: {opendiscourse_sdk.__version__}")
    except Exception as e:
        print(f"  ✗ Main package - {e}")
        all_good = False

    return all_good


def validate_documentation():
    """Validate that documentation exists and is reasonable."""
    print("\nValidating documentation...")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    readme_path = os.path.join(base_dir, "README.md")

    all_good = True

    if os.path.exists(readme_path):
        with open(readme_path) as f:
            content = f.read()

        # Check for key sections
        required_sections = [
            "# OpenDiscourse SDK",
            "## Installation",
            "## Quick Start",
            "## Authentication",
            "## Error Handling",
        ]

        for section in required_sections:
            if section in content:
                print(f"  ✓ {section}")
            else:
                print(f"  ✗ {section} - NOT FOUND")
                all_good = False

        # Check word count
        word_count = len(content.split())
        print(f"  ✓ README word count: {word_count}")
        if word_count < 500:
            print("  ⚠ README might be too short")
    else:
        print("  ✗ README.md not found")
        all_good = False

    return all_good


def count_lines():
    """Count lines of code in the SDK."""
    print("\nCounting lines of code...")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    total_lines = 0
    file_count = 0

    for root, dirs, files in os.walk(base_dir):
        # Skip __pycache__ and tests
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git']]

        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath) as f:
                        lines = len(f.readlines())
                        total_lines += lines
                        file_count += 1
                except Exception:
                    pass

    print(f"  Total Python files: {file_count}")
    print(f"  Total lines of code: {total_lines:,}")

    return True


def main():
    """Run all validation checks."""
    print("="*60)
    print("OpenDiscourse SDK Validation")
    print("="*60)

    results = []

    results.append(("Structure", validate_structure()))
    results.append(("Imports", validate_imports()))
    results.append(("Documentation", validate_documentation()))
    results.append(("Metrics", count_lines()))

    print("\n" + "="*60)
    print("Validation Summary")
    print("="*60)

    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {name}: {status}")

    all_passed = all(passed for _, passed in results)

    print("\n" + "="*60)
    if all_passed:
        print("✓ All validations passed!")
        print("SDK is ready for use.")
    else:
        print("✗ Some validations failed.")
        print("Please review the output above.")
    print("="*60 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
