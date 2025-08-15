#!/usr/bin/env python3
"""
Test configuration and fixtures for AnonSuite
"""

import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture(scope="session")
def test_data_dir():
    """Create temporary directory for test data"""
    temp_dir = tempfile.mkdtemp(prefix="anonsuite_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture(scope="session")
def mock_config_dir(test_data_dir):
    """Create mock configuration directory"""
    config_dir = os.path.join(test_data_dir, "config")
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

@pytest.fixture
def mock_anonsuite_config(mock_config_dir):
    """Create mock AnonSuite configuration"""
    from config_manager import ConfigManager
    config = ConfigManager(config_dir=mock_config_dir)
    return config

@pytest.fixture
def mock_tor_process():
    """Mock Tor process for testing"""
    mock_process = Mock()
    mock_process.pid = 12345
    mock_process.returncode = None
    mock_process.poll.return_value = None
    return mock_process

@pytest.fixture
def mock_privoxy_process():
    """Mock Privoxy process for testing"""
    mock_process = Mock()
    mock_process.pid = 12346
    mock_process.returncode = None
    mock_process.poll.return_value = None
    return mock_process

@pytest.fixture
def sample_wifi_networks():
    """Sample WiFi network data for testing"""
    return [
        {
            "ssid": "TestNetwork1",
            "bssid": "00:11:22:33:44:55",
            "channel": 6,
            "signal_level": -45,
            "encryption": "WPA2",
            "frequency": "2.437 GHz"
        },
        {
            "ssid": "TestNetwork2", 
            "bssid": "AA:BB:CC:DD:EE:FF",
            "channel": 11,
            "signal_level": -67,
            "encryption": "Open",
            "frequency": "2.462 GHz"
        },
        {
            "ssid": "TestNetwork3",
            "bssid": "11:22:33:44:55:66",
            "channel": 1,
            "signal_level": -52,
            "encryption": "WPA3",
            "frequency": "2.412 GHz"
        }
    ]

@pytest.fixture
def sample_pixiewps_output():
    """Sample pixiewps output for testing"""
    return {
        "status": "success",
        "stdout": """
Pixiewps 1.4

[*] Running pixie dust attack
[*] Pixie dust attack was successful!
[+] WPS PIN: 12345678
[+] WPA PSK: testpassword123
[+] AP SSID: TestNetwork
        """,
        "stderr": "",
        "return_code": 0,
        "wps_pin": "12345678",
        "psk": "testpassword123",
        "ssid": "TestNetwork"
    }

@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run for testing"""
    with patch('subprocess.run') as mock_run:
        yield mock_run

@pytest.fixture
def mock_os_path_exists():
    """Mock os.path.exists for testing"""
    with patch('os.path.exists') as mock_exists:
        yield mock_exists

@pytest.fixture
def mock_file_operations():
    """Mock file operations for testing"""
    with patch('builtins.open', create=True) as mock_open:
        yield mock_open

@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch, test_data_dir):
    """Setup test environment variables"""
    monkeypatch.setenv('ANONSUITE_TEST_MODE', '1')
    monkeypatch.setenv('ANONSUITE_DATA_DIR', test_data_dir)
    monkeypatch.setenv('ANONSUITE_CONFIG_DIR', os.path.join(test_data_dir, 'config'))

@pytest.fixture
def cli_runner():
    """CLI test runner"""
    from click.testing import CliRunner
    return CliRunner()

# Test markers
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as a security test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "network: mark test as requiring network access"
    )
    config.addinivalue_line(
        "markers", "root: mark test as requiring root privileges"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location"""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "security" in str(item.fspath):
            item.add_marker(pytest.mark.security)
        
        # Add slow marker for tests that might be slow
        if "scan" in item.name or "attack" in item.name:
            item.add_marker(pytest.mark.slow)
        
        # Add network marker for tests requiring network
        if "network" in item.name or "connectivity" in item.name:
            item.add_marker(pytest.mark.network)

# Helper functions for tests
def create_mock_tor_config(config_dir: str) -> str:
    """Create mock Tor configuration file"""
    torrc_content = """
SocksPort 9000
ControlPort 9001
DataDirectory {}/tor_data
Log notice file {}/tor.log
""".format(config_dir, config_dir)
    
    torrc_path = os.path.join(config_dir, "torrc")
    with open(torrc_path, 'w') as f:
        f.write(torrc_content)
    
    return torrc_path

def create_mock_privoxy_config(config_dir: str) -> str:
    """Create mock Privoxy configuration file"""
    privoxy_content = """
listen-address 127.0.0.1:8119
forward-socks5 / 127.0.0.1:9000 .
logfile {}/privoxy.log
""".format(config_dir)
    
    privoxy_path = os.path.join(config_dir, "privoxy.conf")
    with open(privoxy_path, 'w') as f:
        f.write(privoxy_content)
    
    return privoxy_path
