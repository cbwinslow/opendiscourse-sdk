#!/usr/bin/env python3
"""
Test ingestion script for Congress CLI.
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

def test_congress_cli():
    """Test Congress CLI ingestion."""
    print("\n" + "="*70)
    print("TESTING CONGRESS CLI")
    print("="*70)

    tests_passed = 0
    tests_failed = 0

    # Test 1: Ingest 5 bills from Congress 118
    print("\n[Test 1] Ingesting 5 bills from Congress 118...")
    if run_command([
        "python3", "scripts/ingestion/congress_cli.py",
        "ingest-bills",
        "--congress", "118",
        "--limit", "5"
    ]):
        tests_passed += 1
        print("✓ Bills ingestion succeeded")
    else:
        tests_failed += 1
        print("✗ Bills ingestion failed")

    # Test 2: Ingest members from Congress 118
    print("\n[Test 2] Ingesting members from Congress 118...")
    if run_command([
        "python3", "scripts/ingestion/congress_cli.py",
        "ingest-members",
        "--congress", "118",
        "--limit", "10"
    ]):
        tests_passed += 1
        print("✓ Members ingestion succeeded")
    else:
        tests_failed += 1
        print("✗ Members ingestion failed")

    # Test 3: Check status
    print("\n[Test 3] Checking CLI status...")
    if run_command([
        "python3", "scripts/ingestion/congress_cli.py",
        "status"
    ]):
        tests_passed += 1
        print("✓ Status check succeeded")
    else:
        tests_failed += 1
        print("✗ Status check failed")

    # Summary
    print("\n" + "="*70)
    print("CONGRESS CLI TEST SUMMARY")
    print("="*70)
    print(f"Passed: {tests_passed}/3")
    print(f"Failed: {tests_failed}/3")
    print("="*70)

    return tests_failed == 0

if __name__ == "__main__":
    success = test_congress_cli()
    sys.exit(0 if success else 1)
