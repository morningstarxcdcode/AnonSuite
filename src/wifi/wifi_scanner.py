#!/usr/bin/env python3
"""
WiFi Scanner - Network Reconnaissance Module
Part of AnonSuite WiFi Auditing Tools
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class WiFiScanner:
    """Comprehensive WiFi network scanner and analyzer"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Determine project root dynamically
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))  # Go up from src/wifi/
        self.results_dir = os.path.join(project_root, "run", "wifi_scans")
        self.temp_dir = "/tmp/anonsuite_wifi"
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure required directories exist"""
        os.makedirs(self.results_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

    def check_tools(self) -> Dict:
        """Check availability of WiFi scanning tools"""
        tools = {
            "iwlist": False,
            "iwconfig": False,
            "airport": False,  # macOS specific
            "system_profiler": False  # macOS specific
        }

        # Check iwlist
        try:
            result = subprocess.run(["which", "iwlist"], capture_output=True, timeout=5)
            tools["iwlist"] = result.returncode == 0
        except:
            pass

        # Check iwconfig
        try:
            result = subprocess.run(["which", "iwconfig"], capture_output=True, timeout=5)
            tools["iwconfig"] = result.returncode == 0
        except:
            pass

        # Check airport (macOS)
        try:
            airport_path = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
            tools["airport"] = Path(airport_path).exists()
        except:
            pass

        # Check system_profiler (macOS)
        try:
            result = subprocess.run(["which", "system_profiler"], capture_output=True, timeout=5)
            tools["system_profiler"] = result.returncode == 0
        except:
            pass

        return tools

    def get_interfaces(self) -> List[Dict]:
        """Get available wireless interfaces with improved macOS support"""
        interfaces = []

        try:
            if sys.platform == 'darwin':  # macOS
                # Use system_profiler for comprehensive interface detection
                result = subprocess.run([
                    "system_profiler", "SPAirPortDataType", "-json"
                ], capture_output=True, text=True, timeout=15)

                if result.returncode == 0:
                    import json
                    data = json.loads(result.stdout)

                    for item in data.get('SPAirPortDataType', []):
                        interfaces_data = item.get('spairport_airport_interfaces', [])
                        for iface in interfaces_data:
                            interfaces.append({
                                'name': iface.get('_name', 'Unknown'),
                                'type': 'wireless',
                                'standard': '802.11',
                                'status': iface.get('spairport_status', 'unknown'),
                                'card_type': iface.get('spairport_card_type', 'Unknown'),
                                'platform': 'macOS'
                            })

                # Fallback: try to detect common macOS interface names
                if not interfaces:
                    common_macos_interfaces = ['en0', 'en1', 'en2']
                    for iface_name in common_macos_interfaces:
                        try:
                            result = subprocess.run(['ifconfig', iface_name],
                                                  capture_output=True, text=True, timeout=5)
                            if result.returncode == 0 and 'status: active' in result.stdout:
                                interfaces.append({
                                    'name': iface_name,
                                    'type': 'wireless',
                                    'standard': '802.11',
                                    'status': 'active',
                                    'platform': 'macOS'
                                })
                        except:
                            continue

            else:  # Linux
                result = subprocess.run(["iwconfig"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    current_interface = {}
                    for line in result.stdout.split('\n'):
                        if 'IEEE 802.11' in line:
                            if current_interface:
                                interfaces.append(current_interface)

                            interface_name = line.split()[0]
                            current_interface = {
                                'name': interface_name,
                                'type': 'wireless',
                                'standard': '802.11',
                                'status': 'unknown',
                                'platform': 'Linux'
                            }
                        elif current_interface and 'Access Point:' in line:
                            ap_info = line.split('Access Point:')[-1].strip()
                            current_interface['connected_ap'] = ap_info

                    if current_interface:
                        interfaces.append(current_interface)

        except Exception as e:
            self.logger.error(f"Failed to get interfaces: {e}")

        return interfaces

    def scan_networks(self, interface: Optional[str] = None, timeout: int = 30) -> List[Dict]:
        """Scan for nearby WiFi networks with improved macOS support"""
        networks = []

        # Get available interfaces if none specified
        if not interface:
            interfaces = self.get_interfaces()
            if not interfaces:
                self.logger.error("No wireless interfaces found")
                return networks
            interface = interfaces[0]['name']

        self.logger.info(f"Scanning networks on interface: {interface}")

        try:
            # Platform-specific scanning
            if sys.platform == 'darwin':  # macOS
                networks = self._scan_macos_airport(timeout)
                if not networks:
                    # Fallback to system_profiler method
                    networks = self._scan_macos_system_profiler()
            else:  # Linux
                networks = self._scan_linux_iwlist(interface, timeout)

        except subprocess.TimeoutExpired:
            self.logger.error("Network scan timed out")
        except Exception as e:
            self.logger.error(f"Network scan failed: {e}")

        # Save scan results if any found
        if networks:
            self._save_scan_results(networks, interface)
            self.logger.info(f"Found {len(networks)} networks")
        else:
            self.logger.warning("No networks found")

        return networks

    def _scan_linux_iwlist(self, interface: str, timeout: int) -> List[Dict]:
        """Scan networks using Linux iwlist"""
        result = subprocess.run([
            "iwlist", interface, "scan"
        ], capture_output=True, text=True, timeout=timeout)

        if result.returncode == 0:
            return self._parse_iwlist_output(result.stdout)
        else:
            raise Exception(f"iwlist scan failed: {result.stderr}")

    def _scan_macos_system_profiler(self) -> List[Dict]:
        """Scan networks using macOS system_profiler as fallback"""
        networks = []

        try:
            result = subprocess.run([
                "system_profiler", "SPAirPortDataType", "-json"
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)

                # Parse system profiler data
                for item in data.get('SPAirPortDataType', []):
                    interfaces_data = item.get('spairport_airport_interfaces', [])
                    for iface_data in interfaces_data:
                        # Get current network info
                        current_network = iface_data.get('spairport_current_network_information', {})
                        if current_network:
                            network = {
                                'ssid': current_network.get('spairport_network_name', 'Unknown'),
                                'bssid': current_network.get('spairport_bssid', 'Unknown'),
                                'channel': current_network.get('spairport_channel', 0),
                                'signal_level': self._parse_signal_strength(current_network.get('spairport_signal_noise', '')),
                                'encryption': self._parse_macos_security(current_network.get('spairport_security', 'Unknown')),
                                'frequency': '',
                                'quality': '',
                                'cipher': '',
                                'authentication': '',
                                'mode': 'Master',
                                'timestamp': datetime.now().isoformat()
                            }
                            networks.append(network)

        except Exception as e:
            self.logger.error(f"macOS system_profiler scan failed: {e}")

        return networks

    def _parse_signal_strength(self, signal_noise_str: str) -> int:
        """Parse signal strength from macOS format"""
        try:
            # Format is usually like "signal: -45  noise: -92"
            if 'signal:' in signal_noise_str:
                signal_part = signal_noise_str.split('signal:')[1].split()[0]
                return int(signal_part)
        except:
            pass
        return -50  # Default moderate signal

    def _parse_macos_security(self, security_str: str) -> str:
        """Parse security type from macOS format"""
        security_str = security_str.upper()
        if 'WPA3' in security_str:
            return 'WPA3'
        elif 'WPA2' in security_str:
            return 'WPA2'
        elif 'WPA' in security_str:
            return 'WPA'
        elif 'WEP' in security_str:
            return 'WEP'
        elif 'NONE' in security_str or 'OPEN' in security_str:
            return 'Open'
        else:
            return 'Unknown'

    def _parse_iwlist_output(self, output: str) -> List[Dict]:
        """Parse iwlist scan output"""
        networks = []
        current_network = {}

        for line in output.split('\n'):
            line = line.strip()

            if 'Cell' in line and 'Address:' in line:
                if current_network:
                    networks.append(current_network)

                bssid = line.split('Address: ')[-1].strip()
                current_network = {
                    'bssid': bssid,
                    'ssid': '',
                    'channel': 0,
                    'frequency': '',
                    'signal_level': 0,
                    'quality': '',
                    'encryption': 'Open',
                    'cipher': '',
                    'authentication': '',
                    'mode': 'Master',
                    'timestamp': datetime.now().isoformat()
                }

            elif current_network:
                if 'ESSID:' in line:
                    essid = line.split('ESSID:')[-1].strip().strip('"')
                    current_network['ssid'] = essid

                elif 'Channel:' in line:
                    try:
                        channel = int(line.split('Channel:')[-1].split(')')[0])
                        current_network['channel'] = channel
                    except:
                        pass

                elif 'Frequency:' in line:
                    freq = line.split('Frequency:')[-1].split()[0]
                    current_network['frequency'] = freq

                elif 'Signal level=' in line:
                    try:
                        signal = line.split('Signal level=')[-1].split()[0]
                        current_network['signal_level'] = int(signal.replace('dBm', ''))
                    except:
                        pass

                elif 'Quality=' in line:
                    quality = line.split('Quality=')[-1].split()[0]
                    current_network['quality'] = quality

                elif 'Encryption key:on' in line:
                    current_network['encryption'] = 'WEP/WPA'

                elif 'IE: WPA' in line:
                    current_network['encryption'] = 'WPA'

                elif 'IE: IEEE 802.11i/WPA2' in line:
                    current_network['encryption'] = 'WPA2'

                elif 'Group Cipher' in line:
                    cipher = line.split(':')[-1].strip()
                    current_network['cipher'] = cipher

                elif 'Authentication Suites' in line:
                    auth = line.split(':')[-1].strip()
                    current_network['authentication'] = auth

        if current_network:
            networks.append(current_network)

        return networks

    def _scan_macos_airport(self, timeout: int = 30) -> List[Dict]:
        """Scan networks using macOS airport utility with improved parsing"""
        networks = []

        try:
            airport_path = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"

            if not Path(airport_path).exists():
                self.logger.warning("macOS airport utility not found, trying alternative methods")
                return self._scan_macos_alternative()

            # Use airport utility to scan
            result = subprocess.run([
                airport_path, "-s"
            ], capture_output=True, text=True, timeout=timeout)

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')

                if len(lines) < 2:  # No networks found
                    self.logger.info("No networks found by airport utility")
                    return networks

                # Skip header line
                for line in lines[1:]:
                    try:
                        # Parse airport output format
                        # Format: SSID BSSID             RSSI CHANNEL(CC) CC SECURITY
                        parts = line.split()
                        if len(parts) >= 6:
                            ssid = parts[0] if parts[0] != '' else 'Hidden Network'
                            bssid = parts[1]
                            rssi = parts[2]
                            channel_info = parts[3]  # Format: "6(2.4)"
                            cc = parts[4]
                            security = ' '.join(parts[5:])

                            # Extract channel number
                            channel = 0
                            if '(' in channel_info:
                                try:
                                    channel = int(channel_info.split('(')[0])
                                except:
                                    pass

                            # Parse frequency from channel info
                            frequency = ""
                            if '2.4' in channel_info:
                                frequency = "2.4 GHz"
                            elif '5' in channel_info:
                                frequency = "5 GHz"

                            network = {
                                'ssid': ssid,
                                'bssid': bssid,
                                'signal_level': int(rssi) if rssi.lstrip('-').isdigit() else -50,
                                'channel': channel,
                                'frequency': frequency,
                                'encryption': self._parse_macos_security(security),
                                'country_code': cc,
                                'quality': self._calculate_quality_from_rssi(int(rssi) if rssi.lstrip('-').isdigit() else -50),
                                'cipher': '',
                                'authentication': '',
                                'mode': 'Master',
                                'timestamp': datetime.now().isoformat(),
                                'platform': 'macOS'
                            }

                            networks.append(network)

                    except Exception as e:
                        self.logger.debug(f"Failed to parse airport line '{line}': {e}")
                        continue

                self.logger.info(f"Airport utility found {len(networks)} networks")
            else:
                self.logger.warning(f"Airport utility failed: {result.stderr}")
                return self._scan_macos_alternative()

        except subprocess.TimeoutExpired:
            self.logger.error("Airport scan timed out")
        except Exception as e:
            self.logger.error(f"macOS airport scan failed: {e}")
            return self._scan_macos_alternative()

        return networks

    def _scan_macos_alternative(self) -> List[Dict]:
        """Alternative macOS scanning using system commands"""
        networks = []

        try:
            # Try using networksetup to get current network info
            result = subprocess.run([
                "networksetup", "-getairportnetwork", "en0"
            ], capture_output=True, text=True, timeout=10)

            if result.returncode == 0 and "Current Wi-Fi Network:" in result.stdout:
                current_ssid = result.stdout.split("Current Wi-Fi Network:")[-1].strip()

                if current_ssid and current_ssid != "You are not associated with an AirPort network.":
                    # Get more info about current network
                    network = {
                        'ssid': current_ssid,
                        'bssid': 'Unknown',
                        'signal_level': -50,  # Default
                        'channel': 0,
                        'frequency': '',
                        'encryption': 'Unknown',
                        'quality': '50%',
                        'cipher': '',
                        'authentication': '',
                        'mode': 'Master',
                        'timestamp': datetime.now().isoformat(),
                        'platform': 'macOS',
                        'note': 'Currently connected network'
                    }

                    networks.append(network)
                    self.logger.info(f"Found current network: {current_ssid}")

        except Exception as e:
            self.logger.debug(f"Alternative macOS scan failed: {e}")

        return networks

    def _calculate_quality_from_rssi(self, rssi: int) -> str:
        """Calculate signal quality percentage from RSSI"""
        if rssi >= -30:
            return "100%"
        elif rssi >= -50:
            return "75%"
        elif rssi >= -70:
            return "50%"
        elif rssi >= -80:
            return "25%"
        else:
            return "10%"

    def analyze_network(self, bssid: str, networks: List[Dict]) -> Dict:
        """Analyze specific network for security assessment"""
        target_network = None

        for network in networks:
            if network['bssid'].lower() == bssid.lower():
                target_network = network
                break

        if not target_network:
            return {"error": "Network not found"}

        analysis = {
            "basic_info": target_network,
            "security_assessment": {},
            "attack_vectors": [],
            "recommendations": []
        }

        # Security assessment
        encryption = target_network.get('encryption', 'Open').upper()

        if encryption == 'OPEN':
            analysis["security_assessment"]["level"] = "Very Low"
            analysis["attack_vectors"].extend([
                "Man-in-the-middle attacks",
                "Traffic interception",
                "Evil twin attacks"
            ])
            analysis["recommendations"].append("Enable WPA2/WPA3 encryption")

        elif 'WEP' in encryption:
            analysis["security_assessment"]["level"] = "Low"
            analysis["attack_vectors"].extend([
                "WEP key cracking",
                "ARP replay attacks",
                "Chopchop attacks"
            ])
            analysis["recommendations"].append("Upgrade to WPA2/WPA3")

        elif 'WPA' in encryption and 'WPA2' not in encryption:
            analysis["security_assessment"]["level"] = "Medium"
            analysis["attack_vectors"].extend([
                "WPA handshake capture",
                "Dictionary attacks",
                "PMKID attacks"
            ])
            analysis["recommendations"].append("Upgrade to WPA2/WPA3")

        elif 'WPA2' in encryption:
            analysis["security_assessment"]["level"] = "High"
            analysis["attack_vectors"].extend([
                "WPS PIN attacks (if enabled)",
                "PMKID attacks",
                "Brute force attacks"
            ])
            analysis["recommendations"].extend([
                "Disable WPS if enabled",
                "Use strong passwords",
                "Consider WPA3 upgrade"
            ])

        elif 'WPA3' in encryption:
            analysis["security_assessment"]["level"] = "Very High"
            analysis["attack_vectors"].append("Advanced cryptographic attacks (theoretical)")
            analysis["recommendations"].append("Current security is excellent")

        # Signal strength assessment
        signal = target_network.get('signal_level', 0)
        if signal > -30:
            analysis["security_assessment"]["signal_strength"] = "Excellent"
        elif signal > -50:
            analysis["security_assessment"]["signal_strength"] = "Good"
        elif signal > -70:
            analysis["security_assessment"]["signal_strength"] = "Fair"
        else:
            analysis["security_assessment"]["signal_strength"] = "Poor"

        return analysis

    def _save_scan_results(self, networks: List[Dict], interface: str):
        """Save scan results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"wifi_scan_{interface}_{timestamp}.json"
        filepath = os.path.join(self.results_dir, filename)

        scan_data = {
            "timestamp": datetime.now().isoformat(),
            "interface": interface,
            "network_count": len(networks),
            "networks": networks
        }

        try:
            with open(filepath, 'w') as f:
                json.dump(scan_data, f, indent=2)
            self.logger.info(f"Scan results saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to save scan results: {e}")

    def get_scan_history(self, limit: int = 10) -> List[Dict]:
        """Get recent scan history"""
        history = []

        try:
            scan_files = sorted([
                f for f in os.listdir(self.results_dir)
                if f.startswith('wifi_scan_') and f.endswith('.json')
            ], reverse=True)[:limit]

            for filename in scan_files:
                filepath = os.path.join(self.results_dir, filename)
                try:
                    with open(filepath) as f:
                        scan_data = json.load(f)
                        history.append({
                            "filename": filename,
                            "timestamp": scan_data.get("timestamp"),
                            "interface": scan_data.get("interface"),
                            "network_count": scan_data.get("network_count", 0)
                        })
                except Exception as e:
                    self.logger.error(f"Failed to read scan file {filename}: {e}")

        except Exception as e:
            self.logger.error(f"Failed to get scan history: {e}")

        return history

# Test function
def test_wifi_scanner():
    """Test function for WiFi scanner"""
    scanner = WiFiScanner()

    print("Testing WiFi Scanner...")

    # Check tools
    tools = scanner.check_tools()
    print(f"Available tools: {tools}")

    # Get interfaces
    interfaces = scanner.get_interfaces()
    print(f"Available interfaces: {len(interfaces)}")
    for iface in interfaces:
        print(f"  - {iface['name']}: {iface.get('status', 'unknown')}")

    # Quick scan test (limited time)
    if interfaces:
        print(f"Running quick scan on {interfaces[0]['name']}...")
        networks = scanner.scan_networks(interfaces[0]['name'], timeout=10)
        print(f"Found {len(networks)} networks")

        if networks:
            # Analyze first network
            analysis = scanner.analyze_network(networks[0]['bssid'], networks)
            print(f"Sample analysis: {analysis.get('security_assessment', {}).get('level', 'Unknown')}")

    return {"tools": tools, "interfaces": len(interfaces), "test": "completed"}

if __name__ == "__main__":
    test_wifi_scanner()
