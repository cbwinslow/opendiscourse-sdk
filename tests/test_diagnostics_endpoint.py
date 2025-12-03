from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch

from opendiscourse.main import app
from diagnostic_tools.linux_system_diagnostics.python.models import (
    CPUInfo,
    MemoryInfo,
    DiskDevice,
    HardwareInfo,
    SystemReport,
)
from diagnostic_tools.linux_system_diagnostics.python.collector import LinuxDiagnosticCollector

client = TestClient(app)


def sample_report() -> SystemReport:
    return SystemReport(
        hardware=HardwareInfo(
            timestamp=datetime.now(),
            cpu=CPUInfo(),
            memory=MemoryInfo(),
            disks=[DiskDevice(name="sda", size="100G", type="disk")],
            raw_smart="",
        ),
        processes=[],
        network=[],
        kernel={},
        collection_errors=[],
    )


def test_get_diagnostics():
    with patch.object(LinuxDiagnosticCollector, "collect_full_report", return_value=sample_report()):
        response = client.get("/api/v1/diagnostics/")
    assert response.status_code == 200
    body = response.json()
    assert "hardware" in body
    assert "network" in body
