import subprocess
import time
import pytest
import requests
import os
import socket

# Define dynamic path to multitor script
import sys
from pathlib import Path

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent
MULTITOR_SCRIPT = str(PROJECT_ROOT / "src" / "anonymity" / "multitor" / "multitor")
MULTITOR_LOG = str(PROJECT_ROOT / "src" / "anonymity" / "multitor" / "multitor.log")

# Test parameters
TEST_USER = "morningstar" # Replace with your actual username
SOCKS_PORT = 9000
CONTROL_PORT = 9001
PRIVOXY_PORT = 8119

# Check if we're running in CI
IS_CI = os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true' # Assuming you changed Privoxy's port to 8119

@pytest.fixture(scope="module")
def multitor_instance():
    """
    Fixture to check if the multitor process is running.
    Assumes multitor is started manually before running tests.
    """
    print("\nChecking for running multitor processes...")

    # Give services time to start (if just started manually)
    time.sleep(5)

    # Check if processes are running
    tor_running = check_port_listening(SOCKS_PORT) and check_port_listening(CONTROL_PORT)
    privoxy_running = check_port_listening(PRIVOXY_PORT)

    if not tor_running:
        pytest.fail(f"Tor process not found listening on ports {SOCKS_PORT} and {CONTROL_PORT}. Please start multitor manually before running tests.")
    if not privoxy_running:
        pytest.fail(f"Privoxy process not found listening on port {PRIVOXY_PORT}. Please start multitor manually before running tests.")

    print("Multitor processes are running. Proceeding with tests.")

    # Yield None as there's no process object to manage
    yield None

    # Teardown: No process to stop here, as it's assumed to be managed externally.
    # User is responsible for stopping multitor after tests.
    print("\nMultitor processes were assumed to be managed externally. No automatic teardown.")


def check_port_listening(port, host='127.0.0.1'):
    """Checks if a given port is listening."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((host, port))
        s.close()
        return False # Port is free, so nothing is listening
    except socket.error as e:
        if e.errno in [48, 98]: # Address already in use (48 on macOS, 98 on Linux)
            return True # Port is listening
        else:
            print(f"Socket error: {e}")
            return False
    finally:
        s.close()

@pytest.mark.skipif(IS_CI, reason="Skipping network tests in CI environment")
def test_tor_connectivity(multitor_instance):
    """
    Tests if Tor SOCKS proxy is working by routing a request through it.
    """
    print(f"\nTesting Tor connectivity via SOCKS5 proxy on port {SOCKS_PORT}...")
    proxies = {
        'http': f'socks5h://127.0.0.1:{SOCKS_PORT}',
        'https': f'socks5h://127.0.0.1:{SOCKS_PORT}'
    }
    try:
        # Use a Tor check service
        response = requests.get("https://check.torproject.org/api/ip", proxies=proxies, timeout=30)
        response.raise_for_status()
        data = response.json()
        print(f"Tor connectivity test result: {data}")
        assert data.get("IsTor") is True, "Tor proxy is not working or IP is not a Tor exit node."
        print("Tor SOCKS proxy is working correctly.")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to connect through Tor SOCKS proxy: {e}")

@pytest.mark.skipif(IS_CI, reason="Skipping network tests in CI environment")
def test_privoxy_connectivity(multitor_instance):
    """
    Tests if Privoxy HTTP proxy is working.
    """
    print(f"\nTesting Privoxy connectivity on port {PRIVOXY_PORT}...")
    proxies = {
        'http': f'http://127.0.0.1:{PRIVOXY_PORT}',
        'https': f'http://127.0.0.1:{PRIVOXY_PORT}'
    }
    try:
        # Use a simple HTTP check service
        response = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"Privoxy connectivity test result: {data}")
        assert 'origin' in data, "Privoxy HTTP proxy is not working."
        print("Privoxy HTTP proxy is working correctly.")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to connect through Privoxy HTTP proxy: {e}")
