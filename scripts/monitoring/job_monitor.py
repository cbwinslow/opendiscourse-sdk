#!/usr/bin/env python3
"""Simple monitoring script for ingestion jobs.

This script scans a log file for ERROR lines and prints an alert.
It can be extended to integrate with email or messaging services.
"""
import argparse
from pathlib import Path


def check_log(log_path: Path) -> int:
    """Scan the log file for ERROR entries."""
    if not log_path.exists():
        print(f"Log file {log_path} does not exist")
        return 1

    alerts = 0
    for line in log_path.read_text().splitlines():
        if "ERROR" in line.upper():
            print(f"ALERT: {line}")
            alerts += 1
    return alerts


def main() -> None:
    parser = argparse.ArgumentParser(description="Monitor ingestion job logs")
    parser.add_argument("log_file", type=Path, help="Path to ingestion log file")
    args = parser.parse_args()

    alerts = check_log(args.log_file)
    if alerts:
        print(f"Found {alerts} error(s) in {args.log_file}")
    else:
        print("No errors detected")


if __name__ == "__main__":
    main()
