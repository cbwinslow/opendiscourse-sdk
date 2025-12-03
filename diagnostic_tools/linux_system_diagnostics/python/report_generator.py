from dataclasses import asdict
import json
from pathlib import Path
from typing import Dict

from .models import SystemReport


class ReportGenerator:
    """Generate JSON and Markdown reports from a SystemReport."""

    def __init__(self, report: SystemReport) -> None:
        self.report = report

    def generate_reports(self, output_dir: Path) -> Dict[str, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "system_report.json"
        md_path = output_dir / "system_report.md"

        json_path.write_text(json.dumps(asdict(self.report), indent=2, default=str))
        md_path.write_text(self._to_markdown())

        return {"json": json_path, "markdown": md_path}

    def _to_markdown(self) -> str:
        data = asdict(self.report)
        lines = ["# System Report", f"Generated: {self.report.hardware.timestamp.isoformat()}"]
        cpu = data["hardware"]["cpu"]
        lines.append("## CPU")
        for k, v in cpu.items():
            lines.append(f"- **{k}**: {v}")

        mem = data["hardware"]["memory"]
        lines.append("## Memory")
        for k, v in mem.items():
            lines.append(f"- **{k}**: {v}")

        lines.append("## Disks")
        for disk in data["hardware"]["disks"]:
            mount = disk.get("mountpoint") or "-"
            lines.append(f"- {disk['name']} ({disk['size']}) {mount}")

        lines.append("## Network Interfaces")
        for iface in data["network"]:
            lines.append(f"- {iface['name']} {iface['ipv4']} {iface['state']} {iface['speed']}")

        if self.report.collection_errors:
            lines.append("## Errors")
            for err in self.report.collection_errors:
                lines.append(f"- {err}")

        return "\n".join(lines)
