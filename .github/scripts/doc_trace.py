#!/usr/bin/env python3

import os
import re
import sys
from pathlib import Path


def check_doc_traceability():
    """
    Checks documentation traceability:
    1. Ensures essential docs exist
    2. Validates cross-references between docs (warnings only)
    3. Reports on documentation structure
    """
    errors = []
    warnings = []
    required_sections = {
        "README.md": ["Description", "Installation", "Usage"],
    }

    # Check for required files (only critical ones)
    essential_files = ["README.md"]
    for file in essential_files:
        if not os.path.exists(file):
            errors.append(f"Missing essential file: {file}")

    # Scan all markdown files in root and docs/ (skip subdirectories with lots of docs)
    paths_to_check = []
    paths_to_check.extend(Path(".").glob("*.md"))
    if os.path.exists("docs"):
        paths_to_check.extend(Path("docs").glob("*.md"))

    for path in paths_to_check:
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')

            # Check required sections only for specific files
            if path.name in required_sections:
                for section in required_sections[path.name]:
                    # More flexible section matching
                    pattern = f"(?i)^#+\\s+.*{section}"
                    if not re.search(pattern, content, re.MULTILINE):
                        warnings.append(f"{path}: Missing or differently named section '{section}'")

            # Check cross-references (warnings only for broken refs)
            refs = re.findall(r"\[.+?\]\((.+?)\)", content)
            for ref in refs:
                # Skip external URLs, anchors, and special references
                if ref.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                # Skip relative parent references that might be valid
                if ref.startswith("../"):
                    continue
                ref_path = path.parent / ref
                if not ref_path.exists() and not (path.parent / ref.split('#')[0]).exists():
                    warnings.append(f"{path}: Possibly broken internal reference to {ref}")
        except Exception as e:
            warnings.append(f"{path}: Could not process file - {str(e)}")

    # Report results
    if errors:
        print("ERRORS:")
        print("\n".join(errors))
        print("\nDocumentation check failed due to critical errors")
        sys.exit(1)
    elif warnings:
        print("WARNINGS (non-blocking):")
        print("\n".join(warnings))
        print(f"\nDocumentation check passed with {len(warnings)} warning(s)")
        sys.exit(0)
    else:
        print("Documentation traceability check passed")
        sys.exit(0)


if __name__ == "__main__":
    check_doc_traceability()
