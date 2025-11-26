#!/usr/bin/env python3

import os
import re
import sys
from pathlib import Path


def check_doc_traceability():
    """
    Checks documentation traceability:
    1. Ensures all docs have required sections
    2. Validates cross-references between docs
    3. Checks version headers are present
    """
    errors = []
    required_sections = {
        "README.md": ["Description", "Installation", "Usage"],
        "CHANGELOG.md": ["Unreleased"],
    }

    # Check for required files
    essential_files = ["README.md", "CHANGELOG.md", "docs/README.md"]
    for file in essential_files:
        if not os.path.exists(file):
            errors.append(f"Missing essential file: {file}")

    # Scan all markdown files
    for path in Path(".").rglob("*.md"):
        content = path.read_text()

        # Check version header
        if not re.search(r"^# .+ v\d+\.\d+\.\d+", content, re.MULTILINE):
            errors.append(f"{path}: Missing version header")

        # Check required sections
        if path.name in required_sections:
            for section in required_sections[path.name]:
                if not re.search(f"^#+\s+{section}", content, re.MULTILINE):
                    errors.append(f"{path}: Missing required section '{section}'")

        # Check cross-references
        refs = re.findall(r"\[.+?\]\((.+?)\)", content)
        for ref in refs:
            if ref.startswith(("http://", "https://")):
                continue
            ref_path = path.parent / ref
            if not ref_path.exists():
                errors.append(f"{path}: Broken internal reference to {ref}")

    # Report results
    if errors:
        print("\n".join(errors))
        sys.exit(1)
    else:
        print("Documentation traceability check passed")


if __name__ == "__main__":
    check_doc_traceability()
