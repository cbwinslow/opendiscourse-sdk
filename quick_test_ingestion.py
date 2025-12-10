#!/usr/bin/env python3
"""
Quick Test Bulk Ingestion - Small sample from each source
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

# Setup API keys
with open(".env", "r") as f:
    for line in f:
        if line.strip() and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip().strip("\"'")

print("🚀 Quick Test Bulk Ingestion")
print("=" * 50)

# Test Congress.gov
print("\n🏛️ Testing Congress.gov ingestion...")
start_time = time.time()
result = subprocess.run(
    [
        "./venv/bin/python3",
        "scripts/data_ingestion/congress_api_ingest.py",
        "--source",
        "congress",
        "--congress",
        "117",
        "--limit",
        "10",
    ],
    capture_output=True,
    text=True,
    timeout=120,
)

duration = time.time() - start_time
if result.returncode == 0:
    print(f"✅ Congress.gov test completed in {duration:.1f}s")
else:
    print(f"❌ Congress.gov test failed: {result.stderr[:200]}")

# Test GovInfo
print("\n📄 Testing GovInfo ingestion...")
start_time = time.time()
result = subprocess.run(
    [
        "./venv/bin/python3",
        "scripts/data_ingestion/congress_api_ingest.py",
        "--source",
        "govinfo",
        "--collection",
        "BILLS",
        "--limit",
        "5",
    ],
    capture_output=True,
    text=True,
    timeout=120,
)

duration = time.time() - start_time
if result.returncode == 0:
    print(f"✅ GovInfo test completed in {duration:.1f}s")
else:
    print(f"❌ GovInfo test failed: {result.stderr[:200]}")

# Test OpenStates (using a working script)
print("\n🏢 Testing OpenStates ingestion...")
start_time = time.time()
result = subprocess.run(
    [
        "./venv/bin/python3",
        "scripts/ingest_openstates_people.py",
        "--jurisdiction",
        "ca",
        "--limit",
        "5",
    ],
    capture_output=True,
    text=True,
    timeout=120,
)

duration = time.time() - start_time
if result.returncode == 0:
    print(f"✅ OpenStates test completed in {duration:.1f}s")
else:
    print(f"❌ OpenStates test failed: {result.stderr[:200]}")

print("\n" + "=" * 50)
print("🎯 Quick tests completed!")
print("📊 Ready for full bulk ingestion")
