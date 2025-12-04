#!/usr/bin/env python3
"""
Comprehensive Test Runner with Detailed Reporting

Runs all test suites (pytest, unittest) and generates comprehensive reports
with pass/fail statistics, error details, and logs.

Usage:
    python3 run_all_tests.py
    python3 run_all_tests.py --verbose
    python3 run_all_tests.py --report-dir reports/
"""

import subprocess
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import argparse


class Colors:
    """ANSI color codes."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class TestRunner:
    """Comprehensive test runner with reporting."""

    def __init__(self, verbose: bool = False, report_dir: Path = None):
        self.verbose = verbose
        self.report_dir = report_dir or Path("test_reports")
        self.report_dir.mkdir(parents=True, exist_ok=True)

        self.results = {
            "timestamp": datetime.now().isoformat(),
            "suites": {},
            "summary": {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
        }

    def print_header(self, text: str):
        """Print formatted header."""
        print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{text}{Colors.END}")
        print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")

    def print_status(self, message: str, status: str):
        """Print status message with color."""
        if status == "OK":
            print(f"{Colors.GREEN}✓{Colors.END} {message}")
        elif status == "FAIL":
            print(f"{Colors.RED}✗{Colors.END} {message}")
        elif status == "SKIP":
            print(f"{Colors.YELLOW}⊘{Colors.END} {message}")
        else:
            print(f"{Colors.BLUE}ℹ{Colors.END} {message}")

    def run_pytest(self) -> Tuple[bool, Dict[str, Any]]:
        """Run pytest suite with coverage."""
        self.print_header("Running pytest Suite")

        cmd = [
            "pytest",
            "tests/unit/",
            "-v",
            "--cov=scripts",
            "--cov-report=term-missing",
            "--cov-report=html:test_reports/coverage",
            "--html=test_reports/pytest_report.html",
            "--self-contained-html",
            "--json-report",
            "--json-report-file=test_reports/pytest_results.json"
        ]

        if self.verbose:
            cmd.append("-vv")

        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            duration = time.time() - start_time

            # Parse results
            stats = {
                "exit_code": result.returncode,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "passed": 0,
                "failed": 0,
                "skipped": 0
            }

            # Try to parse JSON report
            json_report = self.report_dir / "pytest_results.json"
            if json_report.exists():
                with open(json_report) as f:
                    pytest_data = json.load(f)
                    summary = pytest_data.get("summary", {})
                    stats["passed"] = summary.get("passed", 0)
                    stats["failed"] = summary.get("failed", 0)
                    stats["skipped"] = summary.get("skipped", 0)
                    stats["total"] = summary.get("total", 0)

            # Print results
            print(f"\nPytest Results:")
            print(f"  Duration: {duration:.2f}s")
            print(f"  Passed: {Colors.GREEN}{stats['passed']}{Colors.END}")
            print(f"  Failed: {Colors.RED}{stats['failed']}{Colors.END}")
            print(f"  Skipped: {Colors.YELLOW}{stats['skipped']}{Colors.END}")

            if result.returncode == 0:
                self.print_status("Pytest suite passed", "OK")
                return True, stats
            else:
                self.print_status("Pytest suite failed", "FAIL")
                if self.verbose:
                    print(f"\n{Colors.RED}STDOUT:{Colors.END}\n{result.stdout}")
                    print(f"\n{Colors.RED}STDERR:{Colors.END}\n{result.stderr}")
                return False, stats

        except subprocess.TimeoutExpired:
            self.print_status("Pytest suite timed out", "FAIL")
            return False, {"error": "timeout"}
        except FileNotFoundError:
            self.print_status("pytest not found - skipping", "SKIP")
            return False, {"error": "not_found"}

    def run_unittest(self) -> Tuple[bool, Dict[str, Any]]:
        """Run unittest discovery."""
        self.print_header("Running unittest Suite")

        cmd = [
            "python3",
            "-m",
            "unittest",
            "discover",
            "-s", "tests",
            "-p", "test_*.py",
            "-v" if self.verbose else "-q"
        ]

        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            duration = time.time() - start_time

            stats = {
                "exit_code": result.returncode,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

            print(f"\nUnittest Results:")
            print(f"  Duration: {duration:.2f}s")

            if result.returncode == 0:
                self.print_status("Unittest suite passed", "OK")
                return True, stats
            else:
                self.print_status("Unittest suite failed", "FAIL")
                if self.verbose:
                    print(f"\n{Colors.RED}Output:{Colors.END}\n{result.stdout}")
                return False, stats

        except FileNotFoundError:
            self.print_status("unittest not available - skipping", "SKIP")
            return False, {"error": "not_found"}

    def check_code_quality(self) -> Tuple[bool, Dict[str, Any]]:
        """Run code quality checks."""
        self.print_header("Code Quality Checks")

        quality_results = {}
        all_passed = True

        # Ruff linting
        print("Running ruff linter...")
        try:
            result = subprocess.run(
                ["ruff", "check", "scripts/"],
                capture_output=True,
                text=True,
                timeout=60
            )
            quality_results["ruff"] = {
                "passed": result.returncode == 0,
                "output": result.stdout
            }
            if result.returncode == 0:
                self.print_status("Ruff linting passed", "OK")
            else:
                self.print_status(f"Ruff found {result.stdout.count('error')} issues", "FAIL")
                all_passed = False
        except FileNotFoundError:
            self.print_status("Ruff not installed - skipping", "SKIP")

        # Type checking with mypy
        print("Running mypy type checker...")
        try:
            result = subprocess.run(
                ["mypy", "scripts/", "--ignore-missing-imports"],
                capture_output=True,
                text=True,
                timeout=120
            )
            quality_results["mypy"] = {
                "passed": result.returncode == 0,
                "output": result.stdout
            }
            if result.returncode == 0:
                self.print_status("Type checking passed", "OK")
            else:
                self.print_status("Type checking found issues", "FAIL")
                all_passed = False
        except FileNotFoundError:
            self.print_status("Mypy not installed - skipping", "SKIP")

        return all_passed, quality_results

    def generate_report(self):
        """Generate comprehensive HTML report."""
        report_path = self.report_dir / "test_summary.html"

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>OpenDiscourse Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .stat-box {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-box.passed {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }}
        .stat-box.failed {{ background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }}
        .stat-number {{ font-size: 48px; font-weight: bold; }}
        .stat-label {{ font-size: 14px; text-transform: uppercase; opacity: 0.9; }}
        .suite {{ margin: 20px 0; padding: 15px; background: #f9f9f9; border-left: 4px solid #4CAF50; }}
        .suite.failed {{ border-left-color: #f44336; }}
        .details {{ margin: 10px 0; padding: 10px; background: #fff; border: 1px solid #ddd; border-radius: 4px; }}
        pre {{ background: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 4px; overflow-x: auto; }}
        .timestamp {{ color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>OpenDiscourse Test Report</h1>
        <p class="timestamp">Generated: {self.results['timestamp']}</p>

        <div class="summary">
            <div class="stat-box">
                <div class="stat-number">{self.results['summary']['total']}</div>
                <div class="stat-label">Total Tests</div>
            </div>
            <div class="stat-box passed">
                <div class="stat-number">{self.results['summary']['passed']}</div>
                <div class="stat-label">Passed</div>
            </div>
            <div class="stat-box failed">
                <div class="stat-number">{self.results['summary']['failed']}</div>
                <div class="stat-label">Failed</div>
            </div>
        </div>

        <h2>Test Suites</h2>
"""

        for suite_name, suite_data in self.results['suites'].items():
            status_class = "failed" if not suite_data.get('passed', False) else ""
            html += f"""
        <div class="suite {status_class}">
            <h3>{suite_name}</h3>
            <div class="details">
                <strong>Status:</strong> {'✓ Passed' if suite_data.get('passed') else '✗ Failed'}<br>
                <strong>Duration:</strong> {suite_data.get('duration', 0):.2f}s
            </div>
        </div>
"""

        html += """
    </div>
</body>
</html>
"""

        with open(report_path, 'w') as f:
            f.write(html)

        print(f"\n📊 HTML report generated: {report_path}")

    def run_all(self):
        """Run all test suites."""
        self.print_header("🧪 OpenDiscourse Comprehensive Test Suite")

        overall_start = time.time()

        # Run pytest
        pytest_passed, pytest_stats = self.run_pytest()
        self.results['suites']['pytest'] = {
            "passed": pytest_passed,
            **pytest_stats
        }

        if 'total' in pytest_stats:
            self.results['summary']['total'] += pytest_stats['total']
            self.results['summary']['passed'] += pytest_stats['passed']
            self.results['summary']['failed'] += pytest_stats['failed']

        # Run unittest
        unittest_passed, unittest_stats = self.run_unittest()
        self.results['suites']['unittest'] = {
            "passed": unittest_passed,
            **unittest_stats
        }

        # Code quality
        quality_passed, quality_stats = self.check_code_quality()
        self.results['suites']['quality'] = {
            "passed": quality_passed,
            **quality_stats
        }

        # Overall summary
        overall_duration = time.time() - overall_start

        self.print_header("📊 Test Summary")
        print(f"Total Duration: {overall_duration:.2f}s")
        print(f"Total Tests: {self.results['summary']['total']}")
        print(f"Passed: {Colors.GREEN}{self.results['summary']['passed']}{Colors.END}")
        print(f"Failed: {Colors.RED}{self.results['summary']['failed']}{Colors.END}")

        # Generate reports
        self.generate_report()

        # Write JSON summary
        json_path = self.report_dir / "test_summary.json"
        with open(json_path, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"📄 JSON report: {json_path}")

        # Exit code
        all_passed = all(s.get('passed', False) for s in self.results['suites'].values())

        if all_passed:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All tests passed!{Colors.END}")
            return 0
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}✗ Some tests failed{Colors.END}")
            return 1


def main():
    parser = argparse.ArgumentParser(description="Run all test suites with reporting")
    parser.add_argument('-v', '--verbose', action='store_true', help="Verbose output")
    parser.add_argument('--report-dir', type=Path, default="test_reports", help="Report directory")

    args = parser.parse_args()

    runner = TestRunner(verbose=args.verbose, report_dir=args.report_dir)
    exit_code = runner.run_all()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
