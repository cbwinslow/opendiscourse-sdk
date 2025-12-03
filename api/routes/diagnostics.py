from dataclasses import asdict
from fastapi import APIRouter
from diagnostic_tools.linux_system_diagnostics.python import LinuxDiagnosticCollector

router = APIRouter(prefix="/diagnostics", tags=["Diagnostics"])


@router.get("/")
async def get_diagnostics() -> dict:
    """Run diagnostics collection and return the system report."""
    collector = LinuxDiagnosticCollector()
    report = collector.collect_full_report()
    return asdict(report)
