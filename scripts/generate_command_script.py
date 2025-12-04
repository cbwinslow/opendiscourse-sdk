#!/usr/bin/env python3
"""
Command Bootstrap Generator

Takes a command with a range and generates individual commands.
Example: "ingest-bills 2005-2024" → generates script with one command per year

Usage:
    python3 generate_command_script.py "ingest-bills 2005-2024" --output commands.sh
    python3 generate_command_script.py --interactive
"""

import argparse
import re
from pathlib import Path
from typing import List, Tuple, Optional
import sys


def parse_range(range_str: str) -> List[int]:
    """
    Parse a range string into individual values.

    Examples:
        "2005-2024" → [2005, 2006, ..., 2024]
        "115-118" → [115, 116, 117, 118]
        "2020,2022,2024" → [2020, 2022, 2024]
        "118" → [118]
    """
    values = []

    # Handle comma-separated
    if ',' in range_str:
        for part in range_str.split(','):
            values.extend(parse_range(part.strip()))
        return sorted(set(values))

    # Handle range
    if '-' in range_str:
        parts = range_str.split('-')
        if len(parts) == 2:
            try:
                start = int(parts[0])
                end = int(parts[1])
                return list(range(start, end + 1))
            except ValueError:
                pass

    # Single value
    try:
        return [int(range_str)]
    except ValueError:
        return []


def extract_range_from_command(command: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Extract range parameter from command.

    Returns:
        (base_command, range_value, parameter_name)
    """
    # Try to find year ranges (4 digits)
    year_pattern = r'(\d{4})-(\d{4})'
    year_match = re.search(year_pattern, command)
    if year_match:
        range_val = f"{year_match.group(1)}-{year_match.group(2)}"
        return (command.replace(range_val, '{value}'), range_val, 'year')

    # Try to find congress/session ranges (2-3 digits)
    congress_pattern = r'(\d{2,3})-(\d{2,3})'
    congress_match = re.search(congress_pattern, command)
    if congress_match:
        range_val = f"{congress_match.group(1)}-{congress_match.group(2)}"
        return (command.replace(range_val, '{value}'), range_val, 'congress')

    # Try to find comma-separated values
    comma_pattern = r'(\d+,\d+(?:,\d+)*)'
    comma_match = re.search(comma_pattern, command)
    if comma_match:
        range_val = comma_match.group(1)
        return (command.replace(range_val, '{value}'), range_val, 'value')

    # No range found
    return (command, None, None)


def generate_command_script(
    base_command: str,
    values: List[int],
    output_file: Optional[Path] = None,
    reverse: bool = False,
    parallel: bool = False
) -> List[str]:
    """
    Generate list of individual commands.

    Args:
        base_command: Command template with {value} placeholder
        values: List of values to substitute
        output_file: Output file path (optional)
        reverse: Process in reverse order (newest first)
        parallel: Generate parallel execution format

    Returns:
        List of commands
    """
    if reverse:
        values = sorted(values, reverse=True)

    commands = []

    for value in values:
        cmd = base_command.replace('{value}', str(value))
        commands.append(cmd)

    # Write to file if specified
    if output_file:
        with open(output_file, 'w') as f:
            f.write(f"#!/bin/bash\n")
            f.write(f"# Generated command script\n")
            f.write(f"# Base command: {base_command}\n")
            f.write(f"# Total commands: {len(commands)}\n\n")

            if parallel:
                f.write("# Execute in parallel\n")
                for cmd in commands:
                    f.write(f"{cmd} &\n")
                f.write("\nwait  # Wait for all background jobs\n")
            else:
                f.write("# Execute sequentially\n")
                for cmd in commands:
                    f.write(f"{cmd}\n")

        output_file.chmod(0o755)  # Make executable
        print(f"✓ Generated {len(commands)} commands in {output_file}")

    return commands


def main():
    parser = argparse.ArgumentParser(
        description="Generate individual commands from range-based command",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Generate script for bills 2005-2024
    %(prog)s "python3 congress_cli.py ingest-bills 2005-2024" -o ingest_all_years.sh

    # Generate for congresses 115-118
    %(prog)s "congress_cli.py ingest-members 115-118" -o ingest_members.sh

    # Reverse order (newest first)
    %(prog)s "ingest-bills 2020-2024" -o ingest.sh --reverse

    # Parallel execution
    %(prog)s "ingest-bills 2020-2024" -o ingest.sh --parallel

    # Interactive mode
    %(prog)s --interactive
        """
    )

    parser.add_argument(
        'command',
        nargs='?',
        help='Command with range (e.g., "ingest-bills 2005-2024")'
    )
    parser.add_argument(
        '-o', '--output',
        type=Path,
        help='Output script file'
    )
    parser.add_argument(
        '--reverse',
        action='store_true',
        help='Process in reverse order (newest first)'
    )
    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Generate parallel execution script'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Interactive mode'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show commands without writing file'
    )

    args = parser.parse_args()

    # Interactive mode
    if args.interactive or not args.command:
        print("🚀 Command Bootstrap Generator (Interactive Mode)\n")
        command = input("Enter command with range: ").strip()

        if not command:
            print("Error: No command provided")
            sys.exit(1)

        reverse = input("Reverse order? (y/N): ").strip().lower() == 'y'
        parallel = input("Parallel execution? (y/N): ").strip().lower() == 'y'
        output = input("Output file (default: commands.sh): ").strip() or "commands.sh"

        args.command = command
        args.reverse = reverse
        args.parallel = parallel
        args.output = Path(output)

    # Extract range from command
    base_command, range_str, param_name = extract_range_from_command(args.command)

    if not range_str:
        print(f"Error: No range found in command: {args.command}")
        print("Expected format: command with year range (2005-2024) or number range (115-118)")
        sys.exit(1)

    # Parse range
    values = parse_range(range_str)

    if not values:
        print(f"Error: Could not parse range: {range_str}")
        sys.exit(1)

    print(f"\n📋 Command Breakdown:")
    print(f"Base: {base_command}")
    print(f"Range: {range_str} ({param_name})")
    print(f"Values: {len(values)} items")
    print(f"Order: {'Reverse (newest first)' if args.reverse else 'Forward (oldest first)'}")
    print(f"Mode: {'Parallel' if args.parallel else 'Sequential'}\n")

    # Generate commands
    if args.dry_run:
        commands = generate_command_script(base_command, values, None, args.reverse, args.parallel)
        print("Generated commands (dry run):")
        for i, cmd in enumerate(commands, 1):
            print(f"{i:3d}. {cmd}")
    else:
        output_file = args.output or Path("commands.sh")
        commands = generate_command_script(
            base_command,
            values,
            output_file,
            args.reverse,
            args.parallel
        )

        print(f"\n✓ Script generated: {output_file}")
        print(f"  Total commands: {len(commands)}")
        print(f"\nRun with: ./{output_file}")


if __name__ == "__main__":
    main()
