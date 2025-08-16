#!/usr/bin/env python3
"""
WiFiPumpkin3 Wrapper - Rogue AP Framework Interface
Part of AnonSuite WiFi Auditing Tools
"""

import subprocess
import logging
import os
import json
import signal
import time
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

class WiFiPumpkinWrapper:
    """Wrapper for WiFiPumpkin3 rogue AP framework"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.wifipumpkin_path = "/Users/morningstar/Desktop/AnonSuite/src/wifi/wifipumpkin3"
        self.python_cmd = "python3"
        self.results_dir = "/Users/morningstar/Desktop/AnonSuite/run/wifipumpkin_results"
        self.config_dir = "/Users/morningstar/Desktop/AnonSuite/config/wifipumpkin"
        self.process = None
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure required directories exist"""
        os.makedirs(self.results_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
    
    def check_dependencies(self) -> Dict:
        """Check if WiFiPumpkin3 and its dependencies are available"""
        status = {
            "wifipumpkin3_available": False,
            "python3_available": False,
            "dependencies_installed": False,
            "issues": []
        }
        
        # Check if wifipumpkin3 directory exists
        if not Path(self.wifipumpkin_path).is_dir():
            status["issues"].append(f"WiFiPumpkin3 directory not found: {self.wifipumpkin_path}")
            return status
        
        status["wifipumpkin3_available"] = True
        
        # Check Python3
        try:
            result = subprocess.run([self.python_cmd, "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                status["python3_available"] = True
            else:
                status["issues"].append("Python3 not available")
        except Exception as e:
            status["issues"].append(f"Python3 check failed: {e}")
        
        # Check WiFiPumpkin3 dependencies
        try:
            result = subprocess.run([
                self.python_cmd, "-c", 
                "import PyQt5; import scapy; import netfilterqueue; print('Dependencies OK')"
            ], capture_output=True, text=True, timeout=10, cwd=self.wifipumpkin_path)
            
            if result.returncode == 0:
                status["dependencies_installed"] = True
            else:
                status["issues"].append(f"Missing dependencies: {result.stderr}")
        except Exception as e:
            status["issues"].append(f"Dependency check failed: {e}")
        
        return status
    
    def get_version(self) -> Optional[str]:
        """Get WiFiPumpkin3 version"""
        try:
            result = subprocess.run([
                self.python_cmd, "-m", "wifipumpkin3", "--version"
            ], capture_output=True, text=True, timeout=10, cwd=self.wifipumpkin_path)
            
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            self.logger.error(f"Failed to get WiFiPumpkin3 version: {e}")
        
        return None
    
    def create_ap_config(self, ssid: str, interface: str, channel: int = 6, 
                        security: str = "WPA2", password: Optional[str] = None) -> str:
        """Create AP configuration file"""
        config = {
            "ap_config": {
                "ssid": ssid,
                "interface": interface,
                "channel": channel,
                "security": security,
                "password": password or "password123",
                "hidden": False
            },
            "plugins": {
                "captiveportal": True,
                "dnsmasq": True,
                "hostapd": True
            },
            "logging": {
                "level": "INFO",
                "file": os.path.join(self.results_dir, f"wifipumpkin_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
            }
        }
        
        config_file = os.path.join(self.config_dir, f"ap_config_{ssid}.json")
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            self.logger.info(f"AP configuration saved to {config_file}")
            return config_file
        except Exception as e:
            self.logger.error(f"Failed to create AP config: {e}")
            raise
    
    def start_ap(self, ssid: str, interface: str, channel: int = 6,
                security: str = "WPA2", password: Optional[str] = None,
                captive_portal: bool = True) -> Dict:
        """Start rogue access point"""
        
        # Check dependencies first
        dep_status = self.check_dependencies()
        if not all([dep_status["wifipumpkin3_available"], 
                   dep_status["python3_available"],
                   dep_status["dependencies_installed"]]):
            return {
                "status": "error",
                "message": "Dependencies not met",
                "issues": dep_status["issues"]
            }
        
        try:
            # Create configuration
            config_file = self.create_ap_config(ssid, interface, channel, security, password)
            
            # Build command
            command = [
                self.python_cmd, "-m", "wifipumpkin3",
                "--interface", interface,
                "--ssid", ssid,
                "--channel", str(channel)
            ]
            
            if captive_portal:
                command.extend(["--captive-portal"])
            
            self.logger.info(f"Starting WiFiPumpkin3 AP: {ssid}")
            self.logger.debug(f"Command: {' '.join(command)}")
            
            # Start the process
            self.process = subprocess.Popen(
                command,
                cwd=self.wifipumpkin_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Give it a moment to start
            time.sleep(3)
            
            # Check if process is still running
            if self.process.poll() is None:
                return {
                    "status": "success",
                    "message": f"Rogue AP '{ssid}' started successfully",
                    "pid": self.process.pid,
                    "config_file": config_file,
                    "interface": interface,
                    "ssid": ssid,
                    "channel": channel
                }
            else:
                stdout, stderr = self.process.communicate()
                return {
                    "status": "error",
                    "message": "Failed to start AP",
                    "stdout": stdout,
                    "stderr": stderr
                }
        
        except Exception as e:
            self.logger.error(f"Error starting WiFiPumpkin3: {e}")
            return {"status": "error", "message": str(e)}
    
    def stop_ap(self) -> Dict:
        """Stop the running access point"""
        if not self.process:
            return {"status": "error", "message": "No AP process running"}
        
        try:
            # Send SIGTERM to the process group
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            
            # Wait for process to terminate
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate gracefully
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                self.process.wait()
            
            self.process = None
            self.logger.info("WiFiPumpkin3 AP stopped")
            
            return {"status": "success", "message": "AP stopped successfully"}
        
        except Exception as e:
            self.logger.error(f"Error stopping AP: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_status(self) -> Dict:
        """Get current AP status"""
        if not self.process:
            return {"status": "stopped", "message": "No AP process running"}
        
        if self.process.poll() is None:
            return {
                "status": "running",
                "pid": self.process.pid,
                "message": "AP is running"
            }
        else:
            return {
                "status": "stopped", 
                "message": "AP process has terminated",
                "return_code": self.process.returncode
            }
    
    def list_interfaces(self) -> List[str]:
        """List available wireless interfaces"""
        interfaces = []
        
        try:
            # Use iwconfig to list wireless interfaces
            result = subprocess.run(["iwconfig"], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'IEEE 802.11' in line:
                        interface = line.split()[0]
                        interfaces.append(interface)
            
        except Exception as e:
            self.logger.error(f"Failed to list interfaces: {e}")
        
        return interfaces
    
    def scan_networks(self, interface: str) -> List[Dict]:
        """Scan for nearby networks"""
        networks = []
        
        try:
            # Use iwlist to scan for networks
            result = subprocess.run([
                "iwlist", interface, "scan"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Parse iwlist output (simplified)
                current_network = {}
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    
                    if 'Cell' in line and 'Address:' in line:
                        if current_network:
                            networks.append(current_network)
                        current_network = {
                            'bssid': line.split('Address: ')[-1],
                            'ssid': '',
                            'channel': '',
                            'signal': '',
                            'encryption': ''
                        }
                    elif 'ESSID:' in line:
                        essid = line.split('ESSID:')[-1].strip('"')
                        current_network['ssid'] = essid
                    elif 'Channel:' in line:
                        channel = line.split('Channel:')[-1].split(')')[0]
                        current_network['channel'] = channel
                    elif 'Signal level=' in line:
                        signal = line.split('Signal level=')[-1].split()[0]
                        current_network['signal'] = signal
                    elif 'Encryption key:' in line:
                        if 'on' in line:
                            current_network['encryption'] = 'WEP/WPA'
                        else:
                            current_network['encryption'] = 'Open'
                
                if current_network:
                    networks.append(current_network)
        
        except Exception as e:
            self.logger.error(f"Failed to scan networks: {e}")
        
        return networks

# Test function
def test_wifipumpkin_wrapper():
    """Test function for WiFiPumpkin wrapper"""
    wrapper = WiFiPumpkinWrapper()
    
    print("Testing WiFiPumpkin3 Wrapper...")
    
    # Check dependencies
    dep_status = wrapper.check_dependencies()
    print(f"Dependencies status: {dep_status}")
    
    # Get version
    version = wrapper.get_version()
    if version:
        print(f"Version: {version}")
    
    # List interfaces
    interfaces = wrapper.list_interfaces()
    print(f"Available interfaces: {interfaces}")
    
    return dep_status

if __name__ == "__main__":
    test_wifipumpkin_wrapper()
