#!/usr/bin/env python3
"""
Bulk All Data Ingestion Executor
Simple script to execute comprehensive bulk ingestion of ALL data types
"""

import subprocess
import sys
import time
from datetime import datetime

def run_bulk_ingestion():
    """Run comprehensive bulk ingestion of all voting data"""

    print("🚀 BULK ALL VOTING DATA INGESTION")
    print("=" * 50)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")

    # Available ingestion modes
    modes = {
        "1": {
            "name": "Congress Votes Only (116-118)",
            "command": ["python3", "scripts/bulk_voting_ingestion.py", "--mode", "congress", "116-118"]
        },
        "2": {
            "name": "All Voting Data (All Sources, Recent Years)",
            "command": ["python3", "scripts/bulk_voting_ingestion.py", "--mode", "votes-only", "--parallel", "--workers", "4"]
        },
        "3": {
            "name": "Complete Full Dataset (All Years, All Sources)",
            "command": ["python3", "scripts/bulk_voting_ingestion.py", "--mode", "full", "--parallel", "--workers", "8"]
        },
        "4": {
            "name": "All Data Types (Bills, Members, Votes, etc.)",
            "command": ["python3", "scripts/bulk_voting_ingestion.py", "--all-data-types"]
        },
        "5": {
            "name": "Dry Run - Show Plan Only",
            "command": ["python3", "scripts/bulk_voting_ingestion.py", "--dry-run"]
        }
    }

    print("Available ingestion options:")
    for key, mode in modes.items():
        print(f"  {key}. {mode['name']}")

    print("")
    choice = input("Select option (1-5): ").strip()

    if choice not in modes:
        print("❌ Invalid choice")
        return

    selected_mode = modes[choice]
    print(f"\n🎯 Running: {selected_mode['name']}")
    print(f"Command: {' '.join(selected_mode['command'])}")
    print("")

    try:
        # Execute the ingestion
        start_time = time.time()
        result = subprocess.run(
            selected_mode['command'],
            capture_output=False,
            text=True
        )

        end_time = time.time()
        duration = end_time - start_time

        print("")
        print("=" * 50)
        print(f"✅ INGESTION COMPLETED")
        print(f"Duration: {duration:.1f} seconds")
        print(f"Exit Code: {result.returncode}")

        if result.returncode == 0:
            print("🎉 SUCCESS: Bulk voting ingestion completed successfully!")
        else:
            print("❌ FAILED: Bulk voting ingestion encountered errors")

    except KeyboardInterrupt:
        print("\n🛑 Ingestion cancelled by user")
    except Exception as e:
        print(f"❌ Error running ingestion: {e}")

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        # Direct mode execution
        mode = sys.argv[1]

        mode_commands = {
            "congress": ["python3", "scripts/bulk_voting_ingestion.py", "--mode", "congress", "116-118"],
            "votes": ["python3", "scripts/bulk_voting_ingestion.py", "--mode", "votes-only", "--parallel", "--workers", "4"],
            "full": ["python3", "scripts/bulk_voting_ingestion.py", "--mode", "full", "--parallel", "--workers", "8"],
            "all": ["python3", "scripts/bulk_voting_ingestion.py", "--all-data-types"],
            "dry-run": ["python3", "scripts/bulk_voting_ingestion.py", "--dry-run"]
        }

        if mode in mode_commands:
            print(f"🚀 Running {mode} mode bulk ingestion...")
            subprocess.run(mode_commands[mode])
        else:
            print(f"❌ Unknown mode: {mode}")
            print(f"Available modes: {', '.join(mode_commands.keys())}")
    else:
        # Interactive mode
        run_bulk_ingestion()

if __name__ == "__main__":
    main()
