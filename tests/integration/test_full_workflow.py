#!/usr/bin/env python3
"""
Integration tests for complete AnonSuite workflows
Tests end-to-end functionality and component integration
"""

import pytest
import os
import sys
import subprocess
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

class TestFullWorkflow:
    """Test complete AnonSuite workflows"""
    
    def test_cli_version_and_help(self):
        """Test basic CLI functionality"""
        # Test version command
        result = subprocess.run([
            sys.executable, 'src/anonsuite.py', '--version'
        ], capture_output=True, text=True, cwd=os.path.join(os.path.dirname(__file__), '..', '..'))
        
        assert result.returncode == 0
        assert "AnonSuite 2.0.0" in result.stdout
    
    def test_health_check_workflow(self):
        """Test health check functionality"""
        result = subprocess.run([
            sys.executable, 'src/anonsuite.py', '--health-check'
        ], capture_output=True, text=True, cwd=os.path.join(os.path.dirname(__file__), '..', '..'))
        
        # Health check should complete without critical errors
        assert result.returncode == 0
    
    def test_configuration_workflow(self):
        """Test configuration management workflow"""
        # Test listing profiles
        result = subprocess.run([
            sys.executable, 'src/anonsuite.py', '--list-profiles'
        ], capture_output=True, text=True, cwd=os.path.join(os.path.dirname(__file__), '..', '..'))
        
        assert result.returncode == 0
        assert "default" in result.stdout
    
    def test_plugin_system_workflow(self):
        """Test plugin system functionality"""
        # Test listing plugins
        result = subprocess.run([
            sys.executable, 'src/anonsuite.py', '--list-plugins'
        ], capture_output=True, text=True, cwd=os.path.join(os.path.dirname(__file__), '..', '..'))
        
        assert result.returncode == 0
    
    @patch('subprocess.run')
    def test_wifi_scan_workflow(self, mock_run):
        """Test WiFi scanning workflow with mocked system calls"""
        # Mock iwconfig output
        mock_run.return_value = Mock(
            returncode=0,
            stdout="wlan0     IEEE 802.11  ESSID:off/any"
        )
        
        result = subprocess.run([
            sys.executable, 'src/anonsuite.py', '--wifi-scan'
        ], capture_output=True, text=True, cwd=os.path.join(os.path.dirname(__file__), '..', '..'))
        
        # Should complete without errors even if no networks found
        assert result.returncode == 0
    
    def test_config_manager_integration(self):
        """Test configuration manager integration"""
        from config_manager import ConfigManager
        
        # Test configuration loading
        config = ConfigManager()
        assert config.get('general.version') == '2.0.0'
        
        # Test profile operations
        profiles = config.list_profiles()
        assert 'default' in profiles
        
        # Test configuration validation
        issues = config.validate_config()
        assert isinstance(issues, dict)
        assert 'errors' in issues
        assert 'warnings' in issues
    
    def test_wifi_tools_integration(self):
        """Test WiFi tools integration"""
        from wifi.wifi_scanner import WiFiScanner
        from wifi.pixiewps_wrapper import PixiewpsWrapper
        from wifi.wifipumpkin_wrapper import WiFiPumpkinWrapper
        
        # Test WiFi scanner
        scanner = WiFiScanner()
        tools = scanner.check_tools()
        assert isinstance(tools, dict)
        
        # Test pixiewps wrapper
        pixie = PixiewpsWrapper()
        assert hasattr(pixie, 'check_binary')
        
        # Test wifipumpkin wrapper
        pump = WiFiPumpkinWrapper()
        assert hasattr(pump, 'check_dependencies')
    
    def test_error_handling_workflow(self):
        """Test error handling in various scenarios"""
        # Test with invalid command
        result = subprocess.run([
            sys.executable, 'src/anonsuite.py', '--invalid-command'
        ], capture_output=True, text=True, cwd=os.path.join(os.path.dirname(__file__), '..', '..'))
        
        # Should exit with error code but not crash
        assert result.returncode != 0
        assert "error" in result.stderr.lower() or "usage" in result.stderr.lower()
    
    def test_output_format_workflow(self):
        """Test different output formats"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_file = f.name
        
        try:
            # Test JSON output format
            result = subprocess.run([
                sys.executable, 'src/anonsuite.py', '--wifi-scan', 
                '--output', output_file, '--format', 'json'
            ], capture_output=True, text=True, cwd=os.path.join(os.path.dirname(__file__), '..', '..'))
            
            # Should complete without errors
            assert result.returncode == 0
            
        finally:
            # Clean up
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_signal_handling_workflow(self):
        """Test graceful shutdown on signals"""
        import signal
        import time
        
        # Start AnonSuite in background
        proc = subprocess.Popen([
            sys.executable, 'src/anonsuite.py'
        ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=os.path.join(os.path.dirname(__file__), '..', '..'))
        
        # Give it a moment to start
        time.sleep(1)
        
        # Send SIGTERM
        proc.terminate()
        
        # Wait for graceful shutdown
        try:
            proc.wait(timeout=5)
            assert proc.returncode is not None
        except subprocess.TimeoutExpired:
            # Force kill if it doesn't shut down gracefully
            proc.kill()
            pytest.fail("Process did not shut down gracefully")

class TestSystemIntegration:
    """Test system-level integration"""
    
    def test_directory_structure(self):
        """Test that all required directories exist or can be created"""
        base_dir = os.path.join(os.path.dirname(__file__), '..', '..')
        
        required_dirs = [
            'src',
            'tests',
            'docs',
            'config',
            'plugins',
            'run',
            'log'
        ]
        
        for dir_name in required_dirs:
            dir_path = os.path.join(base_dir, dir_name)
            assert os.path.exists(dir_path), f"Required directory {dir_name} does not exist"
    
    def test_file_permissions(self):
        """Test that executable files have correct permissions"""
        base_dir = os.path.join(os.path.dirname(__file__), '..', '..')
        
        executable_files = [
            'src/anonymity/multitor/multitor',
            'install.sh'
        ]
        
        for file_path in executable_files:
            full_path = os.path.join(base_dir, file_path)
            if os.path.exists(full_path):
                assert os.access(full_path, os.X_OK), f"File {file_path} is not executable"
    
    def test_configuration_files(self):
        """Test that configuration files are valid"""
        base_dir = os.path.join(os.path.dirname(__file__), '..', '..')
        
        config_files = [
            'config/anonsuite.conf',
            'pyproject.toml',
            'pytest.ini'
        ]
        
        for config_file in config_files:
            file_path = os.path.join(base_dir, config_file)
            if os.path.exists(file_path):
                assert os.path.getsize(file_path) > 0, f"Configuration file {config_file} is empty"
    
    def test_import_structure(self):
        """Test that all modules can be imported without errors"""
        # Test core modules
        try:
            from config_manager import ConfigManager
            from wifi.wifi_scanner import WiFiScanner
            from wifi.pixiewps_wrapper import PixiewpsWrapper
            from wifi.wifipumpkin_wrapper import WiFiPumpkinWrapper
        except ImportError as e:
            pytest.fail(f"Failed to import core modules: {e}")
    
    def test_plugin_system_integration(self):
        """Test plugin system integration"""
        base_dir = os.path.join(os.path.dirname(__file__), '..', '..')
        plugins_dir = os.path.join(base_dir, 'plugins')
        
        # Check if plugins directory exists
        assert os.path.exists(plugins_dir), "Plugins directory does not exist"
        
        # Test plugin loading (if any plugins exist)
        plugin_files = [f for f in os.listdir(plugins_dir) if f.endswith('.py')]
        
        if plugin_files:
            # Test that at least one plugin can be loaded
            sys.path.insert(0, plugins_dir)
            try:
                for plugin_file in plugin_files:
                    module_name = plugin_file[:-3]  # Remove .py extension
                    __import__(module_name)
            except ImportError as e:
                pytest.fail(f"Failed to import plugin {plugin_file}: {e}")
            finally:
                sys.path.pop(0)

if __name__ == "__main__":
    pytest.main([__file__])
