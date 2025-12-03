import streamlit as st
import subprocess
import os
from datetime import datetime

def run_command(command):
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True
    )
    return result.stdout

def kernel_info():
    st.header("Kernel & System Information")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Basic System Info")
        info = run_command("uname -a")
        st.code(info)

    with col2:
        st.subheader("System Uptime")
        uptime = run_command("uptime -s")
        st.code(uptime)

    st.subheader("Running Processes")
    processes = run_command("ps aux --sort -%cpu | head -n 20")
    st.code(processes)

def hardware_info():
    st.header("Hardware Information")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("CPU Information")
        cpu_info = run_command("lscpu")
        st.code(cpu_info)

    with col2:
        st.subheader("Memory Information")
        memory_info = run_command("free -h")
        st.code(memory_info)

    st.subheader("Disk Information")
    disk_info = run_command("df -h")
    st.code(disk_info)

def networking_info():
    st.header("Networking Information")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Interface Statistics")
        interface_stats = run_command("ifconfig")
        st.code(interface_stats)

    with col2:
        st.subheader("Routing Table")
        route_table = run_command("netstat -rn")
        st.code(route_table)

    st.subheader("Open Ports")
    open_ports = run_command("ss -tuln")
    st.code(open_ports)

def main():
    st.title("Linux System Diagnostic TUI")
    st.sidebar.header("Navigation")
    navigation = st.sidebar.radio("Go to:", ["Kernel", "Hardware", "Networking", "Storage"])

    if navigation == "Kernel":
        kernel_info()
    elif navigation == "Hardware":
        hardware_info()
    elif navigation == "Networking":
        networking_info()
    # Add more sections as needed

if __name__ == "__main__":
    main()
