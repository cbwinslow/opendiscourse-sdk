#!/usr/bin/env python3
"""
Test ingestion script for GovInfo CLI.
Tests basic functionality with small data samples.
"""

import sys
import subprocess
from pathlib import Path

def run_command(cmd):
    """Run command and return result."""
    print(f"\n{'='*70}")
    print(f"Running: {' '.join(cmd)}")
    print('='*70)

    result = subprocess.run(cmd, capture_output=True, text=True)

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    return result.returncode == 0

def test_govinfo_cli():
    """Test GovInfo CLI ingestion."""
    print("\n" + "="*70)
    print("TESTING GOVINFO CLI")
    print("="*70)

    tests_passed = 0
    tests_failed = 0

    # Test 1: List collections
    print("\n[Test 1] Listing available collections...")
    if run_command([
        "python3", "scripts/ingestion/govinfo_cli.py",
        "list-collections"
    ]):
        tests_passed += 1
        print("✓ List collections succeeded")
    else:
        tests_failed += 1
        print("✗ List collections failed")

    # Test 2: Ingest 5 packages from BILLS collection
    print("\n[Test 2] Ingesting 5 packages from BILLS collection...")
    if run_command([
        "python3", "scripts/ingestion/govinfo_cli.py",
        "ingest-packages",
        "--collection", "BILLS",
        "--limit", "5"
    ]):
        tests_passed += 1
        print("✓ Package ingestion succeeded")
    else:
        tests_failed += 1
        print("✗ Package ingestion failed")

    #Test 3: Get collection summary
    print("\n[Test 3] Getting BILLS collection summary...")
    if run_command([
        "python3", "scripts/ingestion/govinfo_cli.py",
        "get-collection",
        "--collection", "BILLS"
    ]):
        tests_passed += 1
        print("✓ Collection summary succeeded")
    else:
        tests_failed += 1
        print("✗ Collection summary failed")

    # Summary
    print("\n" + "="*70)
    print("GOVINFO CLI TEST SUMMARY")
    print("="*70)
    print(f"Passed: {tests_passed}/3")
    print(f"Failed: {tests_failed}/3")
    print("="*70)

    return tests_failed == 0

if __name__ == "__main__":
    success = test_govinfo_cli()
    sys.exit(0 if success else 1)
