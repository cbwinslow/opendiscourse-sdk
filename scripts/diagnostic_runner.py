#!/usr/bin/env python3
from pathlib import Path

from diagnostic_tools.linux_system_diagnostics.python import (
    LinuxDiagnosticCollector,
    ReportGenerator,
)


def main():
    collector = LinuxDiagnosticCollector()
    report = collector.collect_full_report()

    generator = ReportGenerator(report)
    outputs = generator.generate_reports(
        output_dir=Path(__file__).parent.parent / "diagnostic_reports"
    )

    print("Generated reports at:")
    for fmt, path in outputs.items():
        print(f"- {fmt.upper()}: {path}")


if __name__ == "__main__":
    main()
