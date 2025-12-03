"""Unit tests for the Linux diagnostics collector."""

import pytest
from unittest.mock import patch, MagicMock
from diagnostic_tools.linux_system_diagnostics.python.collector import LinuxDiagnosticCollector
from diagnostic_tools.linux_system_diagnostics.python.models import CPUInfo, MemoryInfo


class TestLinuxDiagnosticCollector:
    """Test cases for the Linux diagnostic collector."""

    def setup_method(self):
        """Set up test fixtures."""
        self.collector = LinuxDiagnosticCollector()

    def test_collector_initialization(self):
        """Test that collector initializes correctly."""
        assert self.collector.errors == []

    def test_execute_shell_command_success(self):
        """Test successful shell command execution."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = "test output"
            mock_run.return_value.stderr = ""
            
            stdout, stderr = self.collector.execute_shell_command(['echo', 'test'])
            
            assert stdout == "test output"
            assert stderr is None
            assert len(self.collector.errors) == 0

    def test_execute_shell_command_failure(self):
        """Test shell command execution failure."""
        with patch('subprocess.run') as mock_run:
            from subprocess import CalledProcessError
            mock_run.side_effect = CalledProcessError(1, 'cmd', stderr="error message")
            
            stdout, stderr = self.collector.execute_shell_command(['false'])
            
            assert stdout is None
            assert stderr == "error message"
            assert len(self.collector.errors) == 1
            assert "failed" in self.collector.errors[0].lower()

    def test_execute_shell_command_not_found(self):
        """Test shell command not found."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            
            stdout, stderr = self.collector.execute_shell_command(['nonexistent_command'])
            
            assert stdout is None
            assert "Command not found" in stderr
            assert len(self.collector.errors) == 1

    def test_parse_lscpu(self):
        """Test parsing lscpu output."""
        lscpu_output = """Architecture:        x86_64
CPU op-mode(s):      32-bit, 64-bit
Byte Order:          Little Endian
CPU(s):              8
On-line CPU(s) list: 0-7
Thread(s) per core:  2
Core(s) per socket:  4
Socket(s):           1
NUMA node(s):        1
Vendor ID:           GenuineIntel
CPU family:          6
Model:               142
Model name:          Intel(R) Core(TM) i7-8565U CPU @ 1.80GHz
Stepping:            12
CPU MHz:             1800.000
CPU max MHz:         4600.0000
CPU min MHz:         400.0000"""

        cpu_info = self.collector.parse_lscpu(lscpu_output)
        
        assert isinstance(cpu_info, CPUInfo)
        assert cpu_info.model == "Intel(R) Core(TM) i7-8565U CPU @ 1.80GHz"
        assert cpu_info.architecture == "x86_64"
        assert cpu_info.cores == 8
        assert cpu_info.sockets == 1
        assert cpu_info.threads_per_core == 2
        assert cpu_info.max_frequency == "4600.0000"

    def test_parse_sensors(self):
        """Test parsing sensors output."""
        sensors_output = """coretemp-isa-0000
Adapter: ISA adapter
Package id 0:  +45.0°C  (high = +100.0°C, crit = +100.0°C)
Core 0:        +43.0°C  (high = +100.0°C, crit = +100.0°C)
Core 1:        +41.0°C  (high = +100.0°C, crit = +100.0°C)
Core 2:        +42.0°C  (high = +100.0°C, crit = +100.0°C)
Core 3:        +39.0°C  (high = +100.0°C, crit = +100.0°C)"""

        temperatures = self.collector.parse_sensors(sensors_output)
        
        assert len(temperatures) >= 5
        assert 45.0 in temperatures
        assert 43.0 in temperatures
        assert 41.0 in temperatures
        assert all(isinstance(temp, float) for temp in temperatures)

    def test_collect_hardware_info(self):
        """Test collecting comprehensive hardware info."""
        with patch.object(self.collector, 'execute_shell_command') as mock_cmd:
            # Mock lscpu output
            mock_cmd.return_value = ("""Architecture:        x86_64
CPU(s):              4
Socket(s):           1
Thread(s) per core:  1
Model name:          Test CPU
CPU max MHz:         2000.0000""", None)
            
            hardware_info = self.collector.collect_hardware_info()
            
            assert hardware_info is not None
            assert hardware_info.cpu.model == "Test CPU"
            assert hardware_info.cpu.cores == 4
            assert hardware_info.memory is not None
            assert isinstance(hardware_info.disks, list)

    def test_collect_network_info(self):
        """Test collecting network interface information."""
        with patch.object(self.collector, 'execute_shell_command') as mock_cmd:
            # Mock ip output
            mock_cmd.return_value = (
                "2: eth0    inet 192.168.1.100/24 brd 192.168.1.255 scope global UP,LOWER_UP eth0\n"
                "3: wlan0   inet 10.0.0.50/24 brd 10.0.0.255 scope global UP,LOWER_UP wlan0", 
                None
            )
            
            network_info = self.collector.collect_network_info()
            
            assert len(network_info) == 2
            assert network_info[0].name == "eth0"
            assert network_info[0].state == "up"
            assert network_info[0].ipv4 == "192.168.1.100/24"
            assert network_info[1].name == "wlan0"

    def test_collect_full_report(self):
        """Test generating a complete system report."""
        with patch.object(self.collector, 'collect_hardware_info') as mock_hw:
            with patch.object(self.collector, 'collect_network_info') as mock_net:
                # Mock return values
                mock_hw_info = MagicMock()
                mock_net_info = [MagicMock()]
                mock_hw.return_value = mock_hw_info
                mock_net.return_value = mock_net_info
                
                report = self.collector.collect_full_report()
                
                assert report is not None
                assert report.hardware == mock_hw_info
                assert report.network == mock_net_info
                assert isinstance(report.processes, list)
                assert isinstance(report.kernel, dict)
                assert isinstance(report.collection_errors, list)

    def test_error_accumulation(self):
        """Test that errors accumulate correctly."""
        with patch('subprocess.run') as mock_run:
            from subprocess import CalledProcessError
            mock_run.side_effect = CalledProcessError(1, 'cmd1', stderr="error1")
            
            # First command fails
            self.collector.execute_shell_command(['cmd1'])
            assert len(self.collector.errors) == 1
            
            # Second command fails
            mock_run.side_effect = CalledProcessError(1, 'cmd2', stderr="error2")
            self.collector.execute_shell_command(['cmd2'])
            assert len(self.collector.errors) == 2
            
            # Verify both errors are captured
            assert "error1" in str(self.collector.errors)
            assert "error2" in str(self.collector.errors)

    def test_memory_info_parsing(self):
        """Test memory information parsing from free command."""
        with patch.object(self.collector, 'execute_shell_command') as mock_cmd:
            # Mock free -h output
            free_output = """              total        used        free      shared  buff/cache   available
Mem:           15Gi       8.1Gi       1.2Gi       419Mi       6.0Gi       6.7Gi
Swap:         2.0Gi          0B       2.0Gi"""
            
            mock_cmd.side_effect = [
                ("test lscpu", None),  # lscpu
                (None, None),          # sensors (not available)
                (free_output, None),   # free -h
                (None, None),          # swapon
                (None, None),          # lsblk
            ]
            
            hardware_info = self.collector.collect_hardware_info()
            
            assert hardware_info.memory.total == "15Gi"
            assert hardware_info.memory.available == "6.7Gi"
            assert hardware_info.memory.swap_total == "2.0Gi"
            assert hardware_info.memory.swap_used == "0B"

    def test_disk_info_parsing(self):
        """Test disk information parsing from lsblk command."""
        with patch.object(self.collector, 'execute_shell_command') as mock_cmd:
            # Mock lsblk output
            lsblk_output = """NAME   SIZE TYPE MOUNTPOINT
sda    500G disk 
├─sda1 100M part /boot
├─sda2  16G part [SWAP]
└─sda3 384G part /
nvme0n1 1T disk
└─nvme0n1p1 1T part /home"""
            
            mock_cmd.side_effect = [
                ("test lscpu", None),     # lscpu
                (None, None),             # sensors
                (None, None),             # free
                (None, None),             # swapon
                (lsblk_output, None),     # lsblk
            ]
            
            hardware_info = self.collector.collect_hardware_info()
            
            assert len(hardware_info.disks) >= 5  # At least 5 disk entries
            disk_names = [disk.name for disk in hardware_info.disks]
            assert "sda" in disk_names
            assert "nvme0n1" in disk_names
