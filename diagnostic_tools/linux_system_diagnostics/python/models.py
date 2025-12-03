"""Data models for Linux system diagnostics collector."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class CPUInfo(BaseModel):
    """CPU information model."""
    model_name: str
    cores: int
    threads: int
    frequency: float
    cache_size: Optional[str] = None
    flags: List[str] = []


class MemoryInfo(BaseModel):
    """Memory information model."""
    total: int
    available: int
    used: int
    free: int
    buffers: int
    cached: int
    swap_total: int
    swap_used: int
    swap_free: int


class DiskDevice(BaseModel):
    """Disk device information model."""
    device: str
    mountpoint: str
    filesystem: str
    size: int
    used: int
    available: int
    use_percent: float


class NetworkInterface(BaseModel):
    """Network interface information model."""
    name: str
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    status: str
    speed: Optional[str] = None
    rx_bytes: int = 0
    tx_bytes: int = 0
    rx_packets: int = 0
    tx_packets: int = 0


class HardwareInfo(BaseModel):
    """Hardware information model."""
    cpu: CPUInfo
    memory: MemoryInfo
    disks: List[DiskDevice]
    network_interfaces: List[NetworkInterface]


class SystemReport(BaseModel):
    """Complete system diagnostic report."""
    timestamp: datetime
    hostname: str
    os_info: Dict[str, Any]
    hardware: HardwareInfo
    uptime: float
    load_average: List[float]
    processes: int
    logged_in_users: int