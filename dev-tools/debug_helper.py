#!/usr/bin/env python3
"""
Debug Helper for AnonSuite Development
Quick debugging utilities that I find myself needing constantly.

TODO: Add more utilities as I find pain points
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import psutil


class DebugHelper:
    """Collection of debugging utilities for AnonSuite development"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent

    def check_system_state(self):
        """Quick system state check - processes, ports, files"""
        print("=== System State Check ===")

        # Check for running processes
        tor_processes = []
        anonsuite_processes = []

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'tor' in proc.info['name'].lower():
                    tor_processes.append(proc.info)
                elif 'anonsuite' in ' '.join(proc.info['cmdline'] or []):
                    anonsuite_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        print(f"Tor processes: {len(tor_processes)}")
        for proc in tor_processes[:3]:  # Show first 3
            print(f"  PID {proc['pid']}: {proc['name']}")

        print(f"AnonSuite processes: {len(anonsuite_processes)}")
        for proc in anonsuite_processes:
            print(f"  PID {proc['pid']}: {' '.join(proc['cmdline'][:2])}")

        # Check important files
        important_files = [
            "src/anonsuite.py",
            "run/status.json",
            "architect-state.json"
        ]

        print("\nImportant files:")
        for file_path in important_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                stat = full_path.stat()
                size = stat.st_size
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%H:%M:%S")
                print(f"  ✓ {file_path} ({size} bytes, modified {mtime})")
            else:
                print(f"  ✗ {file_path} (missing)")

    def show_config_summary(self):
        """Show current configuration summary"""
        print("\n=== Configuration Summary ===")

        # Check environment variables
        env_vars = [
            "ANONSUITE_ENV",
            "ANONSUITE_LOG_LEVEL",
            "ANONSUITE_CONFIG_PATH"
        ]

        print("Environment variables:")
        for var in env_vars:
            value = os.getenv(var, "not set")
            print(f"  {var}: {value}")

        # Check config files
        config_files = [
            "seed/config.yaml",
            ".env.example",
            "run/status.json"
        ]

        print("\nConfig files:")
        for config_file in config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        content = f.read()
                        lines = len(content.split('\n'))
                        print(f"  ✓ {config_file} ({lines} lines)")
                except Exception as e:
                    print(f"  ⚠ {config_file} (error reading: {e})")
            else:
                print(f"  ✗ {config_file} (missing)")

    def test_imports(self):
        """Test if all required Python modules can be imported"""
        print("\n=== Import Test ===")

        # Required modules for AnonSuite
        required_modules = [
            "psutil",
            "yaml",
            "requests",
            "click",  # might be used
            "colorama"  # might be used
        ]

        for module in required_modules:
            try:
                __import__(module)
                print(f"  ✓ {module}")
            except ImportError as e:
                print(f"  ✗ {module} - {e}")

    def check_network_tools(self):
        """Check if required network tools are available"""
        print("\n=== Network Tools Check ===")

        tools = [
            "tor",
            "privoxy",
            "iwconfig",
            "iptables",
            "netstat"
        ]

        for tool in tools:
            try:
                result = subprocess.run(["which", tool],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    path = result.stdout.strip()
                    print(f"  ✓ {tool} -> {path}")
                else:
                    print(f"  ✗ {tool} (not found)")
            except Exception as e:
                print(f"  ⚠ {tool} (error checking: {e})")

    def show_recent_logs(self, lines=10):
        """Show recent log entries"""
        print(f"\n=== Recent Logs (last {lines} lines) ===")

        log_files = [
            "log/multitor.20250811.log",  # might exist
            "/tmp/anonsuite.log",  # might exist
            "/var/log/anonsuite/anonsuite.log"  # might exist
        ]

        found_logs = False
        for log_file in log_files:
            log_path = Path(log_file)
            if not log_path.is_absolute():
                log_path = self.project_root / log_file

            if log_path.exists():
                found_logs = True
                print(f"\nFrom {log_file}:")
                try:
                    with open(log_path) as f:
                        all_lines = f.readlines()
                        recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                        for line in recent_lines:
                            print(f"  {line.rstrip()}")
                except Exception as e:
                    print(f"  Error reading log: {e}")

        if not found_logs:
            print("  No log files found")

    def performance_snapshot(self):
        """Take a quick performance snapshot"""
        print("\n=== Performance Snapshot ===")

        # System resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        print(f"CPU Usage: {cpu_percent}%")
        print(f"Memory: {memory.percent}% used ({memory.used // 1024 // 1024}MB / {memory.total // 1024 // 1024}MB)")
        print(f"Disk: {disk.percent}% used")

        # Network connections (Tor-related ports)
        tor_ports = [9050, 9051, 8118]
        connections = psutil.net_connections()

        print("\nTor-related connections:")
        for conn in connections:
            if conn.laddr and conn.laddr.port in tor_ports:
                status = conn.status if hasattr(conn, 'status') else 'unknown'
                print(f"  Port {conn.laddr.port}: {status}")

    def run_all_checks(self):
        """Run all debugging checks"""
        print("AnonSuite Debug Helper")
        print("=" * 50)

        self.check_system_state()
        self.show_config_summary()
        self.test_imports()
        self.check_network_tools()
        self.show_recent_logs()
        self.performance_snapshot()

        print("\n" + "=" * 50)
        print("Debug check complete!")

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1]
        helper = DebugHelper()

        if command == "system":
            helper.check_system_state()
        elif command == "config":
            helper.show_config_summary()
        elif command == "imports":
            helper.test_imports()
        elif command == "tools":
            helper.check_network_tools()
        elif command == "logs":
            lines = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            helper.show_recent_logs(lines)
        elif command == "perf":
            helper.performance_snapshot()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: system, config, imports, tools, logs, perf")
    else:
        # Run all checks
        helper = DebugHelper()
        helper.run_all_checks()

if __name__ == "__main__":
    main()
