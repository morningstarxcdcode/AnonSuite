#!/usr/bin/env python3
"""
Unit tests for WiFi auditing tools
"""

import json
import os
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest

from wifi.pixiewps_wrapper import PixiewpsWrapper
from wifi.wifi_scanner import WiFiScanner
from wifi.wifipumpkin_wrapper import WiFiPumpkinWrapper


class TestPixiewpsWrapper:
    """Test Pixiewps wrapper functionality"""

    def test_pixiewps_initialization(self):
        """Test Pixiewps wrapper initialization"""
        wrapper = PixiewpsWrapper()

        assert hasattr(wrapper, 'logger')
        assert hasattr(wrapper, 'pixiewps_path')
        assert hasattr(wrapper, 'results_dir')
        assert wrapper.pixiewps_path.endswith('pixiewps')

    @patch('os.path.exists')
    @patch('os.access')
    def test_check_binary_exists(self, mock_access, mock_exists):
        """Test binary existence check"""
        mock_exists.return_value = True
        mock_access.return_value = True

        wrapper = PixiewpsWrapper()
        result = wrapper.check_binary()

        assert result is True
        mock_exists.assert_called_once()
        mock_access.assert_called_once()

    @patch('os.path.exists')
    def test_check_binary_missing(self, mock_exists):
        """Test binary missing scenario"""
        mock_exists.return_value = False

        wrapper = PixiewpsWrapper()
        result = wrapper.check_binary()

        assert result is False

    @patch('os.path.exists')
    @patch('os.access')
    def test_check_binary_not_executable(self, mock_access, mock_exists):
        """Test binary not executable scenario"""
        mock_exists.return_value = True
        mock_access.return_value = False

        wrapper = PixiewpsWrapper()
        result = wrapper.check_binary()

        assert result is False

    @patch.object(PixiewpsWrapper, 'check_binary')
    @patch('subprocess.run')
    def test_run_attack_success(self, mock_run, mock_check_binary, sample_pixiewps_output):
        """Test successful pixiewps attack"""
        mock_check_binary.return_value = True

        # Mock successful subprocess run
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = sample_pixiewps_output['stdout']
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        wrapper = PixiewpsWrapper()

        result = wrapper.run_attack(
            pke="test_pke",
            pkr="test_pkr",
            e_hash1="test_hash1",
            e_hash2="test_hash2",
            authkey="test_authkey",
            e_nonce="test_nonce"
        )

        assert result['status'] == 'success'
        assert 'wps_pin' in result
        assert 'psk' in result
        mock_run.assert_called_once()

    @patch.object(PixiewpsWrapper, 'check_binary')
    def test_run_attack_binary_unavailable(self, mock_check_binary):
        """Test attack when binary is unavailable"""
        mock_check_binary.return_value = False

        wrapper = PixiewpsWrapper()

        result = wrapper.run_attack(
            pke="test_pke",
            pkr="test_pkr",
            e_hash1="test_hash1",
            e_hash2="test_hash2",
            authkey="test_authkey",
            e_nonce="test_nonce"
        )

        assert result['status'] == 'error'
        assert 'not available' in result['message']

    @patch.object(PixiewpsWrapper, 'check_binary')
    @patch('subprocess.run')
    def test_run_attack_timeout(self, mock_run, mock_check_binary):
        """Test attack timeout scenario"""
        mock_check_binary.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired('pixiewps', 300)

        wrapper = PixiewpsWrapper()

        result = wrapper.run_attack(
            pke="test_pke",
            pkr="test_pkr",
            e_hash1="test_hash1",
            e_hash2="test_hash2",
            authkey="test_authkey",
            e_nonce="test_nonce"
        )

        assert result['status'] == 'error'
        assert 'timed out' in result['message']

    def test_parse_results_success(self, sample_pixiewps_output):
        """Test parsing successful pixiewps results"""
        wrapper = PixiewpsWrapper()

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = sample_pixiewps_output['stdout']
        mock_result.stderr = ""

        parsed = wrapper._parse_results(mock_result, ['pixiewps', 'test'])

        assert parsed['status'] == 'success'
        assert parsed['wps_pin'] == '12345678'
        assert parsed['psk'] == 'testpassword123'
        assert parsed['ssid'] == 'TestNetwork'

    def test_parse_results_failure(self):
        """Test parsing failed pixiewps results"""
        wrapper = PixiewpsWrapper()

        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = "Attack failed"
        mock_result.stderr = "Error message"

        parsed = wrapper._parse_results(mock_result, ['pixiewps', 'test'])

        assert parsed['status'] == 'failed'
        assert parsed['return_code'] == 1
        assert parsed['wps_pin'] is None

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_save_results(self, mock_json_dump, mock_file):
        """Test saving attack results"""
        wrapper = PixiewpsWrapper()

        test_results = {"status": "success", "wps_pin": "12345678"}
        wrapper._save_results(test_results)

        mock_file.assert_called_once()
        mock_json_dump.assert_called_once_with(test_results, mock_file(), indent=2)

    @patch.object(PixiewpsWrapper, 'check_binary')
    @patch('subprocess.run')
    def test_get_version(self, mock_run, mock_check_binary):
        """Test getting pixiewps version"""
        mock_check_binary.return_value = True

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Pixiewps 1.4"
        mock_run.return_value = mock_result

        wrapper = PixiewpsWrapper()
        version = wrapper.get_version()

        assert version == "Pixiewps 1.4"

class TestWiFiPumpkinWrapper:
    """Test WiFiPumpkin3 wrapper functionality"""

    def test_wifipumpkin_initialization(self):
        """Test WiFiPumpkin3 wrapper initialization"""
        wrapper = WiFiPumpkinWrapper()

        assert hasattr(wrapper, 'logger')
        assert hasattr(wrapper, 'wifipumpkin_path')
        assert hasattr(wrapper, 'results_dir')
        assert hasattr(wrapper, 'config_dir')
        assert wrapper.process is None

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_check_dependencies_success(self, mock_run, mock_exists):
        """Test successful dependency check"""
        mock_exists.return_value = True

        # Mock successful Python and dependency checks
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Dependencies OK"
        mock_run.return_value = mock_result

        wrapper = WiFiPumpkinWrapper()
        status = wrapper.check_dependencies()

        assert status['wifipumpkin3_available'] is True
        assert status['python3_available'] is True
        assert status['dependencies_installed'] is True
        assert len(status['issues']) == 0

    @patch('os.path.exists')
    def test_check_dependencies_missing_directory(self, mock_exists):
        """Test dependency check with missing directory"""
        mock_exists.return_value = False

        wrapper = WiFiPumpkinWrapper()
        status = wrapper.check_dependencies()

        assert status['wifipumpkin3_available'] is False
        assert len(status['issues']) > 0
        assert any('directory not found' in issue.lower() for issue in status['issues'])

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_check_dependencies_missing_python_deps(self, mock_run, mock_exists):
        """Test dependency check with missing Python dependencies"""
        mock_exists.return_value = True

        # Mock Python available but dependencies missing
        mock_results = [
            Mock(returncode=0, stdout="Python 3.9.0"),  # Python check
            Mock(returncode=1, stderr="ModuleNotFoundError: No module named 'PyQt5'")  # Dependency check
        ]
        mock_run.side_effect = mock_results

        wrapper = WiFiPumpkinWrapper()
        status = wrapper.check_dependencies()

        assert status['python3_available'] is True
        assert status['dependencies_installed'] is False
        assert any('dependencies' in issue.lower() for issue in status['issues'])

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_create_ap_config(self, mock_json_dump, mock_file):
        """Test AP configuration creation"""
        wrapper = WiFiPumpkinWrapper()

        config_file = wrapper.create_ap_config(
            ssid="TestAP",
            interface="wlan0",
            channel=6,
            security="WPA2",
            password="testpass123"
        )

        assert config_file.endswith('.json')
        mock_file.assert_called_once()
        mock_json_dump.assert_called_once()

        # Check that the config data contains expected fields
        config_data = mock_json_dump.call_args[0][0]
        assert config_data['ap_config']['ssid'] == "TestAP"
        assert config_data['ap_config']['interface'] == "wlan0"
        assert config_data['ap_config']['channel'] == 6

    @patch.object(WiFiPumpkinWrapper, 'check_dependencies')
    @patch.object(WiFiPumpkinWrapper, 'create_ap_config')
    @patch('subprocess.Popen')
    @patch('time.sleep')
    def test_start_ap_success(self, mock_sleep, mock_popen, mock_create_config, mock_check_deps):
        """Test successful AP startup"""
        # Mock successful dependency check
        mock_check_deps.return_value = {
            'wifipumpkin3_available': True,
            'python3_available': True,
            'dependencies_installed': True,
            'issues': []
        }

        # Mock config creation
        mock_create_config.return_value = "/path/to/config.json"

        # Mock successful process
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Still running
        mock_popen.return_value = mock_process

        wrapper = WiFiPumpkinWrapper()
        result = wrapper.start_ap("TestAP", "wlan0")

        assert result['status'] == 'success'
        assert result['pid'] == 12345
        assert result['ssid'] == "TestAP"
        assert wrapper.process == mock_process

    @patch.object(WiFiPumpkinWrapper, 'check_dependencies')
    def test_start_ap_dependencies_not_met(self, mock_check_deps):
        """Test AP startup with unmet dependencies"""
        mock_check_deps.return_value = {
            'wifipumpkin3_available': False,
            'python3_available': True,
            'dependencies_installed': False,
            'issues': ['WiFiPumpkin3 not found']
        }

        wrapper = WiFiPumpkinWrapper()
        result = wrapper.start_ap("TestAP", "wlan0")

        assert result['status'] == 'error'
        assert 'dependencies not met' in result['message'].lower()

    def test_stop_ap_no_process(self):
        """Test stopping AP when no process is running"""
        wrapper = WiFiPumpkinWrapper()
        wrapper.process = None

        result = wrapper.stop_ap()

        assert result['status'] == 'error'
        assert 'no ap process' in result['message'].lower()

    @patch('os.killpg')
    @patch('os.getpgid')
    def test_stop_ap_success(self, mock_getpgid, mock_killpg):
        """Test successful AP stop"""
        wrapper = WiFiPumpkinWrapper()

        # Mock running process
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.wait.return_value = None
        wrapper.process = mock_process

        mock_getpgid.return_value = 12345

        result = wrapper.stop_ap()

        assert result['status'] == 'success'
        assert wrapper.process is None
        mock_killpg.assert_called()

    def test_get_status_no_process(self):
        """Test status check with no process"""
        wrapper = WiFiPumpkinWrapper()
        wrapper.process = None

        status = wrapper.get_status()

        assert status['status'] == 'stopped'
        assert 'no ap process' in status['message'].lower()

    def test_get_status_running_process(self):
        """Test status check with running process"""
        wrapper = WiFiPumpkinWrapper()

        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Still running
        wrapper.process = mock_process

        status = wrapper.get_status()

        assert status['status'] == 'running'
        assert status['pid'] == 12345

    @patch('subprocess.run')
    def test_list_interfaces(self, mock_run):
        """Test listing wireless interfaces"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = """
wlan0     IEEE 802.11  ESSID:off/any
          Mode:Managed  Access Point: Not-Associated   Tx-Power=20 dBm
          Retry short limit:7   RTS thr:off   Fragment thr:off
          Encryption key:off
          Power Management:on

wlan1     IEEE 802.11  ESSID:"TestNetwork"
          Mode:Managed  Frequency:2.437 GHz  Access Point: 00:11:22:33:44:55
        """
        mock_run.return_value = mock_result

        wrapper = WiFiPumpkinWrapper()
        interfaces = wrapper.list_interfaces()

        assert 'wlan0' in interfaces
        assert 'wlan1' in interfaces
        assert len(interfaces) == 2

class TestWiFiScanner:
    """Test WiFi scanner functionality"""

    def test_wifi_scanner_initialization(self):
        """Test WiFi scanner initialization"""
        scanner = WiFiScanner()

        assert hasattr(scanner, 'logger')
        assert hasattr(scanner, 'results_dir')
        assert hasattr(scanner, 'temp_dir')

    @patch('subprocess.run')
    def test_check_tools_linux(self, mock_run):
        """Test tool availability check on Linux"""
        # Mock successful tool checks
        mock_run.return_value = Mock(returncode=0)

        scanner = WiFiScanner()
        tools = scanner.check_tools()

        assert isinstance(tools, dict)
        assert 'iwlist' in tools
        assert 'iwconfig' in tools
        assert 'airport' in tools
        assert 'system_profiler' in tools

    @patch('subprocess.run')
    def test_get_interfaces_linux(self, mock_run):
        """Test getting interfaces on Linux"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = """
wlan0     IEEE 802.11  ESSID:off/any
          Mode:Managed  Access Point: Not-Associated   Tx-Power=20 dBm

wlan1     IEEE 802.11  ESSID:"TestNetwork"
          Mode:Managed  Frequency:2.437 GHz  Access Point: 00:11:22:33:44:55
        """
        mock_run.return_value = mock_result

        scanner = WiFiScanner()
        interfaces = scanner.get_interfaces()

        assert len(interfaces) >= 1
        assert any(iface['name'] == 'wlan0' for iface in interfaces)
        assert any(iface['type'] == 'wireless' for iface in interfaces)

    @patch('subprocess.run')
    def test_scan_networks_iwlist(self, mock_run):
        """Test network scanning with iwlist"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = """
wlan0     Scan completed :
          Cell 01 - Address: 00:11:22:33:44:55
                    Channel:6
                    Frequency:2.437 GHz (Channel 6)
                    Quality=70/70  Signal level=-30 dBm
                    ESSID:"TestNetwork1"
                    Encryption key:on
                    IE: IEEE 802.11i/WPA2 Version 1

          Cell 02 - Address: AA:BB:CC:DD:EE:FF
                    Channel:11
                    Frequency:2.462 GHz (Channel 11)
                    Quality=40/70  Signal level=-67 dBm
                    ESSID:"TestNetwork2"
                    Encryption key:off
        """
        mock_run.return_value = mock_result

        scanner = WiFiScanner()
        networks = scanner.scan_networks("wlan0")

        assert len(networks) == 2
        assert networks[0]['ssid'] == "TestNetwork1"
        assert networks[0]['bssid'] == "00:11:22:33:44:55"
        assert networks[0]['channel'] == 6
        assert networks[0]['encryption'] == "WPA2"

        assert networks[1]['ssid'] == "TestNetwork2"
        assert networks[1]['encryption'] == "Open"

    def test_analyze_network(self, sample_wifi_networks):
        """Test network security analysis"""
        scanner = WiFiScanner()

        # Test WPA2 network analysis
        analysis = scanner.analyze_network("00:11:22:33:44:55", sample_wifi_networks)

        assert 'basic_info' in analysis
        assert 'security_assessment' in analysis
        assert 'attack_vectors' in analysis
        assert 'recommendations' in analysis

        assert analysis['basic_info']['ssid'] == "TestNetwork1"
        assert analysis['security_assessment']['level'] == "High"
        assert isinstance(analysis['attack_vectors'], list)
        assert isinstance(analysis['recommendations'], list)

    def test_analyze_network_open(self, sample_wifi_networks):
        """Test analysis of open network"""
        scanner = WiFiScanner()

        # Test open network (TestNetwork2)
        analysis = scanner.analyze_network("AA:BB:CC:DD:EE:FF", sample_wifi_networks)

        assert analysis['security_assessment']['level'] == "Very Low"
        assert "Man-in-the-middle" in analysis['attack_vectors']
        assert any("Enable WPA2/WPA3" in rec for rec in analysis['recommendations'])

    def test_analyze_network_not_found(self, sample_wifi_networks):
        """Test analysis of non-existent network"""
        scanner = WiFiScanner()

        analysis = scanner.analyze_network("FF:FF:FF:FF:FF:FF", sample_wifi_networks)

        assert "error" in analysis
        assert "not found" in analysis["error"].lower()

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_save_scan_results(self, mock_json_dump, mock_file, sample_wifi_networks):
        """Test saving scan results"""
        scanner = WiFiScanner()

        scanner._save_scan_results(sample_wifi_networks, "wlan0")

        mock_file.assert_called_once()
        mock_json_dump.assert_called_once()

        # Check saved data structure
        saved_data = mock_json_dump.call_args[0][0]
        assert 'timestamp' in saved_data
        assert 'interface' in saved_data
        assert 'network_count' in saved_data
        assert 'networks' in saved_data
        assert saved_data['interface'] == "wlan0"
        assert saved_data['network_count'] == len(sample_wifi_networks)

if __name__ == "__main__":
    pytest.main([__file__])
