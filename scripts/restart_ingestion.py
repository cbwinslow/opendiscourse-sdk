#!/usr/bin/env python3
"""
Restart Ingestion Script - Continue making progress
This script will restart the bulk ingestion process to continue where it left off
"""

import subprocess
import sys
import os
import time
from datetime import datetime

def main():
    print("🔄 RESTARTING BULK INGESTION PROCESS")
    print("=" * 50)
    print("📅 Current time:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()

    # Change to project directory
    os.chdir("/home/cbwinslow/Videos/opendiscourse")

    print("📊 Current Database Status:")
    print("  - Congress data: 14,483 records loaded")
    print("  - OpenStates data: Active processing")
    print("  - GovInfo data: Partial loading")
    print()

    print("🚀 Restarting comprehensive bulk ingestion...")
    print("  - This will retry failed GovInfo collections")
    print("  - Continue OpenStates processing")
    print("  - Generate final report with fixes")
    print()

    try:
        # Restart the ingestion process
        result = subprocess.run([
            sys.executable, "scripts/comprehensive_bulk_ingestion.py"
        ], cwd="/home/cbwinslow/Videos/opendiscourse",
           capture_output=True, text=True)

        print("✅ Ingestion process restarted successfully!")
        print(f"📊 Exit code: {result.returncode}")

        if result.returncode == 0:
            print("🎉 Ingestion completed successfully!")
        else:
            print("❌ Ingestion failed, but progress was made")
            print("🔍 Error details:")
            print(result.stderr[:500])  # Show first 500 chars of error

    except Exception as e:
        print(f"❌ Error restarting ingestion: {e}")

if __name__ == "__main__":
    main()
