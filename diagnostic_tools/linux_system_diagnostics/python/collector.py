import subprocess
from datetime import datetime
# Removed unused Path import
from typing import List, Optional, Tuple

from .models import (
    CPUInfo,
    DiskDevice,
    HardwareInfo,
    MemoryInfo,
    NetworkInterface,
    SystemReport,
)


class LinuxDiagnosticCollector:
    def __init__(self):
        self.errors = []

    def execute_shell_command(
        self, command: List[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            return result.stdout.strip(), None
        except subprocess.CalledProcessError as e:
            self.errors.append(
                f"Command '{' '.join(command)}' failed: {e.stderr[:50]}"
            )
            return None, e.stderr
        except FileNotFoundError:
            error_msg = f"Command not found: {command[0]}"
            self.errors.append(error_msg)
            return None, error_msg

    def parse_lscpu(self, output: str) -> CPUInfo:
        cpu_data = {}
        for line in output.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                cpu_data[key.strip()] = value.strip()

        return CPUInfo(
            model=cpu_data.get('Model name', 'Unknown'),
            architecture=cpu_data.get('Architecture', 'Unknown'),
            cores=int(cpu_data.get('CPU(s)', 0)),
            sockets=int(cpu_data.get('Socket(s)', 0)),
            threads_per_core=int(cpu_data.get('Thread(s) per core', 0)),
            max_frequency=cpu_data.get('CPU max MHz', 'Unknown'),
            raw_lscpu=output
        )

    def parse_sensors(self, output: str) -> List[float]:
        temps = []
        for line in output.split('\n'):
            if 'temp' in line.lower():
                parts = line.split()
                for part in parts:
                    if '°C' in part:
                        temp = part.replace('°C', '').replace('+', '')
                        try:
                            temps.append(float(temp))
                        except ValueError:
                            continue
        return temps

    def collect_hardware_info(self) -> HardwareInfo:
        """Collect comprehensive hardware information from system commands."""
        # Collect CPU info
        lscpu_out, _ = self.execute_shell_command(['lscpu'])
        cpu_info = self.parse_lscpu(lscpu_out) if lscpu_out else CPUInfo()

        # Collect temperatures
        sensors_out, _ = self.execute_shell_command(['sensors'])
        if sensors_out:
            cpu_info.temperatures = self.parse_sensors(sensors_out)

        # Collect memory info
        free_out, _ = self.execute_shell_command(['free', '-h'])
        swapon_out, _ = self.execute_shell_command(['swapon', '--show'])

        # Parse memory data
        memory_info = MemoryInfo(
            total='Unknown',
            available='Unknown',
            swap_total='Unknown',
            swap_used='Unknown',
            swapon_output=swapon_out
        )

        if free_out:
            lines = free_out.split('\n')
            if len(lines) >= 2:
                mem = lines[1].split()
                if len(mem) >= 7:
                    memory_info.total = mem[1]
                    memory_info.available = mem[6]

            if len(lines) >= 3:
                swap = lines[2].split()
                if len(swap) >= 3:
                    memory_info.swap_total = swap[1]
                    memory_info.swap_used = swap[2]

        # Collect disk info
        lsblk_out, _ = self.execute_shell_command(['lsblk', '-o', 'NAME,SIZE,TYPE,MOUNTPOINT'])
        disks = []
        if lsblk_out:
            for line in lsblk_out.split('\n')[1:]:  # Skip header
                parts = line.split()
                if len(parts) >= 3:
                    disks.append(DiskDevice(
                        name=parts[0],
                        size=parts[1],
                        type=parts[2],
                        mountpoint=parts[3] if len(parts) > 3 else None
                    ))

        # Collect SMART data
        smart_data = {}
        for disk in [d.name for d in disks if d.type == 'disk']:
            smart_out, err = self.execute_shell_command([
                'sudo', '--non-interactive',
                'smartctl', '-i', f'/dev/{disk}'
            ])
            if err and 'permission' in err.lower():
                self.errors.append(f"Permission denied for smartctl on {disk}")
                smart_out = None
            if smart_out:
                smart_data[disk] = smart_out

        return HardwareInfo(
            timestamp=datetime.now(),
            cpu=cpu_info,
            memory=memory_info,
            disks=disks,
            raw_smart='\n'.join([f"{k}:\n{v}" for k, v in smart_data.items()])
        )

    def collect_network_info(self) -> List[NetworkInterface]:
        """Collect network interface information using ip command."""
        ip_out, _ = self.execute_shell_command(['ip', '-o', '-4', 'addr', 'show'])
        interfaces = []

        if ip_out:
            for line in ip_out.split('\n'):
                parts = line.strip().split()
                if len(parts) >= 6:
                    interface = NetworkInterface(
                        name=parts[1].rstrip(':'),
                        state='up' if 'UP' in parts[2] else 'down',
                        ipv4=parts[3],
                        speed='unknown'
                    )
                    # Get speed
                    ethtool_out, _ = self.execute_shell_command([
                        'ethtool',
                        interface.name
                    ])
                    if ethtool_out:
                        for eth_line in ethtool_out.split('\n'):
                            if 'Speed:' in eth_line:
                                interface.speed = eth_line.split(':')[1].strip()
                    interfaces.append(interface)

        return interfaces

    def collect_full_report(self) -> SystemReport:
        """Generate complete system diagnostics report."""
        return SystemReport(
            hardware=self.collect_hardware_info(),
            processes=[],
            network=self.collect_network_info(),
            kernel={},
            collection_errors=self.errors
        )
