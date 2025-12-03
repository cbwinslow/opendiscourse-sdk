#!/usr/bin/env python3
"""
Test runner script for bulk ingestion tests
Provides a unified interface for running different types of tests
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return the result"""
    print(f"🔄 {description}")
    print(f"   Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
    else:
        print(f"❌ {description} failed")
        if result.stderr:
            print(f"   Error: {result.stderr.strip()}")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")

    return result.returncode == 0

def main():
    parser = argparse.ArgumentParser(description='Bulk Ingestion Test Runner')
    parser.add_argument('test_type', choices=[
        'unit', 'integration', 'performance', 'all', 'coverage', 'report'
    ], help='Type of tests to run')

    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--parallel', '-p', action='store_true',
                       help='Run tests in parallel (if pytest-xdist available)')
    parser.add_argument('--output', '-o', type=str,
                       help='Output directory for reports')

    args = parser.parse_args()

    # Change to test directory
    test_dir = Path(__file__).parent
    os.chdir(test_dir)

    # Base pytest command
    base_cmd = ['pytest']

    if args.verbose:
        base_cmd.extend(['-v', '-s'])
    else:
        base_cmd.append('--tb=short')

    if args.parallel:
        base_cmd.append('-n')
        base_cmd.append('auto')

    # Add output directory
    if args.output:
        os.makedirs(args.output, exist_ok=True)
        base_cmd.extend(['--html', f'{args.output}/test_report.html',
                        '--self-contained-html'])
        base_cmd.extend(['--junit-xml', f'{args.output}/junit.xml'])

    success = True

    if args.test_type == 'unit':
        cmd = base_cmd + ['-m', 'unit and not slow']
        success = run_command(cmd, 'Unit Tests')

    elif args.test_type == 'integration':
        cmd = base_cmd + ['-m', 'integration and not slow and not network']
        success = run_command(cmd, 'Integration Tests')

    elif args.test_type == 'performance':
        cmd = base_cmd + ['-m', 'performance', '--durations=0']
        success = run_command(cmd, 'Performance Tests')

    elif args.test_type == 'all':
        # Run all test types
        print("🧪 Running all tests...")

        # Unit tests
        cmd1 = base_cmd + ['-m', 'unit and not slow']
        if not run_command(cmd1, 'Unit Tests'):
            success = False

        # Integration tests
        cmd2 = base_cmd + ['-m', 'integration and not slow and not network']
        if not run_command(cmd2, 'Integration Tests'):
            success = False

        # Performance tests
        cmd3 = base_cmd + ['-m', 'performance', '--durations=0']
        if not run_command(cmd3, 'Performance Tests'):
            success = False

        # Troubleshooting tests
        cmd4 = base_cmd + ['-m', 'troubleshooting']
        if not run_command(cmd4, 'Troubleshooting Tests'):
            success = False

    elif args.test_type == 'coverage':
        cmd = base_cmd + ['--cov=../../scripts', '--cov-report=term-missing',
                         '--cov-report=html:coverage', '--cov-fail-under=80']
        success = run_command(cmd, 'Coverage Report')

    elif args.test_type == 'report':
        if not args.output:
            print("❌ Please specify output directory with --output")
            return False

        cmd = base_cmd + ['--html', f'{args.output}/test_report.html',
                         '--self-contained-html', '--junit-xml', f'{args.output}/junit.xml']
        success = run_command(cmd, 'Test Report')

    if success:
        print("\n🎉 All tests completed successfully!")
        return 0
    else:
        print("\n💥 Some tests failed. Check the output above for details.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
