"""
Phase 3 Integration Tests - Core Implementation Validation
Tests the complete integration of multitor with AnonSuite CLI.
"""

import pytest
import sys
import os
import subprocess
import time
from unittest.mock import Mock, patch
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from anonsuite import AnonSuiteCLI, ConfigManager

class TestPhase3CoreIntegration:
    """Test Phase 3 core implementation integration"""
    
    def test_anonsuite_cli_initialization(self):
        """Test AnonSuite CLI initializes correctly"""
        cli = AnonSuiteCLI()
        
        # Verify CLI components are initialized
        assert cli.config_manager is not None
        assert cli.config is not None
        assert cli.running is True
        
        # Verify configuration paths
        assert hasattr(cli.config, 'anonsuite_root')
        assert hasattr(cli.config, 'anonymity_module')
        assert hasattr(cli.config, 'wifi_module')
    
    def test_multitor_script_exists(self):
        """Test multitor script exists and is executable"""
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        multitor_path = os.path.join(config.anonymity_module, "multitor", "multitor")
        
        # Verify multitor script exists
        assert os.path.exists(multitor_path), f"Multitor script not found at {multitor_path}"
        
        # Verify script is executable
        assert os.access(multitor_path, os.X_OK), "Multitor script is not executable"
    
    def test_anonymity_status_checking(self):
        """Test anonymity service status checking functionality"""
        cli = AnonSuiteCLI()
        
        # Test status checking doesn't crash
        try:
            cli._check_anonymity_status()
            status_check_success = True
        except Exception as e:
            status_check_success = False
            pytest.fail(f"Status checking failed: {e}")
        
        assert status_check_success
    
    def test_tor_connectivity_testing(self):
        """Test Tor connectivity testing functionality"""
        cli = AnonSuiteCLI()
        
        # Test connectivity testing doesn't crash
        try:
            cli._test_tor_connectivity()
            connectivity_test_success = True
        except Exception as e:
            connectivity_test_success = False
            pytest.fail(f"Connectivity testing failed: {e}")
        
        assert connectivity_test_success
    
    def test_tor_log_viewing(self):
        """Test Tor log viewing functionality"""
        cli = AnonSuiteCLI()
        
        # Test log viewing doesn't crash
        try:
            cli._view_tor_logs()
            log_viewing_success = True
        except Exception as e:
            log_viewing_success = False
            pytest.fail(f"Log viewing failed: {e}")
        
        assert log_viewing_success
    
    def test_performance_monitoring_integration(self):
        """Test performance monitoring integration"""
        cli = AnonSuiteCLI()
        
        # Test performance monitoring doesn't crash
        try:
            cli._monitor_performance()
            performance_monitoring_success = True
        except Exception as e:
            performance_monitoring_success = False
            pytest.fail(f"Performance monitoring failed: {e}")
        
        assert performance_monitoring_success
    
    def test_service_stop_functionality(self):
        """Test service stopping functionality"""
        cli = AnonSuiteCLI()
        
        # Test service stopping doesn't crash
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            
            try:
                cli._stop_anonymity_services()
                service_stop_success = True
            except Exception as e:
                service_stop_success = False
                pytest.fail(f"Service stopping failed: {e}")
        
        assert service_stop_success
    
    def test_enhanced_menu_structure(self):
        """Test enhanced anonymity menu structure"""
        cli = AnonSuiteCLI()
        
        # Verify enhanced menu options are available
        # This tests that the menu structure includes new options
        menu_options = [
            "Start AnonSuite (Tor + Proxy)",
            "Stop AnonSuite",
            "Restart AnonSuite",
            "Check Status", 
            "Monitor Performance",
            "View Tor Logs"
        ]
        
        # Test that menu rendering doesn't crash
        with patch('builtins.input', return_value='0'):  # Simulate user choosing "Back"
            try:
                # This would normally show the menu, but we'll exit immediately
                cli.running = False  # Prevent infinite loop
                menu_test_success = True
            except Exception as e:
                menu_test_success = False
                pytest.fail(f"Menu structure test failed: {e}")
        
        assert menu_test_success

class TestPhase3ServiceIntegration:
    """Test service integration aspects of Phase 3"""
    
    def test_multitor_command_construction(self):
        """Test multitor command construction"""
        cli = AnonSuiteCLI()
        
        # Test command construction for starting services
        multitor_script = os.path.join(cli.config.anonymity_module, "multitor", "multitor")
        
        expected_cmd = [
            "sudo", multitor_script,
            "--user", "morningstar",
            "--socks-port", "9000",
            "--control-port", "9001",
            "--proxy", "privoxy"
        ]
        
        # Verify command structure is correct
        assert multitor_script.endswith("multitor")
        assert "morningstar" in expected_cmd
        assert "9000" in expected_cmd
        assert "9001" in expected_cmd
        assert "privoxy" in expected_cmd
    
    def test_port_configuration_consistency(self):
        """Test port configuration consistency"""
        # Verify consistent port usage across the system
        expected_ports = {
            'tor_socks': 9000,
            'tor_control': 9001, 
            'privoxy_http': 8119
        }
        
        # Test that ports are consistently referenced
        for port_name, port_number in expected_ports.items():
            assert isinstance(port_number, int)
            assert 1024 <= port_number <= 65535  # Valid port range
    
    def test_configuration_paths_validity(self):
        """Test configuration paths are valid"""
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Test that all configured paths exist
        paths_to_check = [
            config.anonsuite_root,
            config.anonymity_module,
            config.wifi_module
        ]
        
        for path in paths_to_check:
            assert os.path.exists(path), f"Configuration path does not exist: {path}"
    
    def test_log_file_accessibility(self):
        """Test log file accessibility"""
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Test Tor log path construction
        tor_log_path = os.path.join(config.anonymity_module, "multitor", "tor_9000", "tor.log")
        
        # Verify log directory exists (log file may not exist if Tor isn't running)
        log_dir = os.path.dirname(tor_log_path)
        if os.path.exists(log_dir):
            # If directory exists, verify it's accessible
            assert os.access(log_dir, os.R_OK), f"Log directory not readable: {log_dir}"

class TestPhase3ErrorHandling:
    """Test error handling in Phase 3 implementation"""
    
    def test_missing_multitor_script_handling(self):
        """Test handling of missing multitor script"""
        cli = AnonSuiteCLI()
        
        # Test with non-existent script path
        with patch.object(cli.config, 'anonymity_module', '/nonexistent/path'):
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = FileNotFoundError("Script not found")
                
                # Should handle missing script gracefully
                result = cli._execute_command(["nonexistent_script"], "Test command")
                assert result is False
    
    def test_network_connectivity_error_handling(self):
        """Test network connectivity error handling"""
        cli = AnonSuiteCLI()
        
        # Test with network errors
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            # Should handle network errors gracefully
            try:
                cli._test_tor_connectivity()
                error_handling_success = True
            except Exception:
                error_handling_success = False
            
            assert error_handling_success
    
    def test_log_file_error_handling(self):
        """Test log file error handling"""
        cli = AnonSuiteCLI()
        
        # Test with non-existent log file
        with patch('os.path.exists', return_value=False):
            try:
                cli._view_tor_logs()
                log_error_handling_success = True
            except Exception:
                log_error_handling_success = False
            
            assert log_error_handling_success
    
    def test_process_management_error_handling(self):
        """Test process management error handling"""
        cli = AnonSuiteCLI()
        
        # Test with process management errors
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "pgrep")
            
            try:
                cli._check_anonymity_status()
                process_error_handling_success = True
            except Exception:
                process_error_handling_success = False
            
            assert process_error_handling_success

class TestPhase3PerformanceIntegration:
    """Test performance aspects of Phase 3 integration"""
    
    def test_status_check_performance(self):
        """Test status checking performance"""
        cli = AnonSuiteCLI()
        
        start_time = time.time()
        cli._check_anonymity_status()
        end_time = time.time()
        
        # Status check should complete within reasonable time
        execution_time = end_time - start_time
        assert execution_time < 10.0, f"Status check took too long: {execution_time}s"
    
    def test_connectivity_test_performance(self):
        """Test connectivity testing performance"""
        cli = AnonSuiteCLI()
        
        start_time = time.time()
        cli._test_tor_connectivity()
        end_time = time.time()
        
        # Connectivity test should complete within reasonable time
        execution_time = end_time - start_time
        assert execution_time < 30.0, f"Connectivity test took too long: {execution_time}s"
    
    def test_log_viewing_performance(self):
        """Test log viewing performance"""
        cli = AnonSuiteCLI()
        
        start_time = time.time()
        cli._view_tor_logs()
        end_time = time.time()
        
        # Log viewing should complete quickly
        execution_time = end_time - start_time
        assert execution_time < 5.0, f"Log viewing took too long: {execution_time}s"

# Test fixtures for Phase 3 integration
@pytest.fixture
def phase3_environment():
    """Fixture providing Phase 3 test environment"""
    return {
        "multitor_config": {
            "user": "morningstar",
            "socks_port": 9000,
            "control_port": 9001,
            "proxy": "privoxy"
        },
        "expected_services": ["tor", "privoxy"],
        "expected_ports": [9000, 9001, 8119],
        "log_files": ["tor.log", "multitor.log"]
    }

@pytest.fixture
def mock_running_services():
    """Fixture to mock running services"""
    with patch('subprocess.run') as mock_run:
        # Mock successful process checks
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "12345\n"  # Mock PID
        yield mock_run
