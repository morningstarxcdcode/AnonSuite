#!/usr/bin/env python3
"""
Unit tests for AnonSuite core functionality
"""

import json
import os
from unittest.mock import MagicMock, Mock, patch

import pytest

from anonsuite import AnonSuiteCLI, VisualTokens
from config_manager import ConfigManager


class TestConfigManager:
    """Test configuration management functionality"""

    def test_config_manager_initialization(self, mock_config_dir):
        """Test ConfigManager initialization"""
        config = ConfigManager(config_dir=mock_config_dir)
        assert config.config_dir == mock_config_dir
        assert config.current_profile == "default"
        assert isinstance(config.config, dict)

    def test_get_config_value(self, mock_anonsuite_config):
        """Test getting configuration values"""
        config = mock_anonsuite_config

        # Test existing value
        version = config.get('general.version')
        assert version == "2.0.0"

        # Test non-existing value with default
        non_existing = config.get('non.existing.key', 'default_value')
        assert non_existing == 'default_value'

        # Test nested value
        tor_port = config.get('anonymity.tor.socks_port')
        assert tor_port == 9000

    def test_set_config_value(self, mock_anonsuite_config):
        """Test setting configuration values"""
        config = mock_anonsuite_config

        # Set new value
        success = config.set('general.debug', True)
        assert success is True
        assert config.get('general.debug') is True

        # Set nested value
        success = config.set('test.nested.value', 'test_value')
        assert success is True
        assert config.get('test.nested.value') == 'test_value'

    def test_profile_operations(self, mock_anonsuite_config):
        """Test profile creation, listing, and deletion"""
        config = mock_anonsuite_config

        # Test profile creation
        success = config.create_profile('test_profile')
        assert success is True

        # Test profile listing
        profiles = config.list_profiles()
        assert 'default' in profiles
        assert 'test_profile' in profiles

        # Test profile deletion
        success = config.delete_profile('test_profile')
        assert success is True

        # Verify deletion
        profiles = config.list_profiles()
        assert 'test_profile' not in profiles

    def test_config_validation(self, mock_anonsuite_config):
        """Test configuration validation"""
        config = mock_anonsuite_config

        issues = config.validate_config()
        assert isinstance(issues, dict)
        assert 'errors' in issues
        assert 'warnings' in issues
        assert 'info' in issues

        # All should be lists
        assert isinstance(issues['errors'], list)
        assert isinstance(issues['warnings'], list)
        assert isinstance(issues['info'], list)

class TestVisualTokens:
    """Test visual design tokens"""

    def test_color_codes(self):
        """Test color code definitions"""
        assert 'primary' in VisualTokens.COLORS
        assert 'error' in VisualTokens.COLORS
        assert 'success' in VisualTokens.COLORS
        assert 'reset' in VisualTokens.COLORS

        # Test that colors are ANSI escape codes
        assert VisualTokens.COLORS['primary'].startswith('\033[')
        assert VisualTokens.COLORS['reset'] == '\033[0m'

    def test_symbols(self):
        """Test symbol definitions"""
        assert 'success' in VisualTokens.SYMBOLS
        assert 'error' in VisualTokens.SYMBOLS
        assert 'warning' in VisualTokens.SYMBOLS
        assert 'info' in VisualTokens.SYMBOLS

        # Test that symbols are strings
        assert isinstance(VisualTokens.SYMBOLS['success'], str)
        assert isinstance(VisualTokens.SYMBOLS['error'], str)

class TestAnonSuiteCLI:
    """Test main CLI functionality"""

    @patch('anonsuite.ConfigManager')
    @patch('anonsuite.PluginManager')
    def test_cli_initialization(self, mock_plugin_manager, mock_config_manager):
        """Test CLI initialization"""
        cli = AnonSuiteCLI()

        # Verify initialization
        assert hasattr(cli, 'config')
        assert hasattr(cli, 'plugin_manager')
        assert hasattr(cli, 'running')
        assert cli.running is True

    @patch('anonsuite.ConfigManager')
    @patch('anonsuite.PluginManager')
    def test_colorize_method(self, mock_plugin_manager, mock_config_manager):
        """Test text colorization"""
        cli = AnonSuiteCLI()

        # Test colorization
        colored_text = cli._colorize("test text", "primary")
        assert "test text" in colored_text
        assert VisualTokens.COLORS['primary'] in colored_text
        assert VisualTokens.COLORS['reset'] in colored_text

    @patch('anonsuite.ConfigManager')
    @patch('anonsuite.PluginManager')
    @patch('builtins.input', return_value='1')
    def test_get_user_choice(self, mock_input, mock_plugin_manager, mock_config_manager):
        """Test user input handling"""
        cli = AnonSuiteCLI()

        choice = cli._get_user_choice()
        assert choice == 1

    @patch('anonsuite.ConfigManager')
    @patch('anonsuite.PluginManager')
    @patch('builtins.input', return_value='invalid')
    def test_get_user_choice_invalid(self, mock_input, mock_plugin_manager, mock_config_manager):
        """Test invalid user input handling"""
        cli = AnonSuiteCLI()

        choice = cli._get_user_choice()
        assert choice == -1  # Should return -1 for invalid input

class TestProgressSpinner:
    """Test progress spinner functionality"""

    def test_spinner_initialization(self):
        """Test spinner initialization"""
        from anonsuite import ProgressSpinner

        spinner = ProgressSpinner("Testing...")
        assert spinner.message == "Testing..."
        assert spinner.running is False
        assert spinner.spinner_thread is None

    def test_spinner_characters(self):
        """Test spinner character sequence"""
        from anonsuite import ProgressSpinner

        spinner = ProgressSpinner("Test")
        expected_chars = ['|', '/', '-', '\\']
        assert spinner.spinner_chars == expected_chars

class TestExceptionHandling:
    """Test custom exception classes"""

    def test_anonsuite_error(self):
        """Test AnonSuiteError exception"""
        from anonsuite import AnonSuiteError

        error = AnonSuiteError("Test error", "E001", {"detail": "test"})
        assert error.message == "Test error"
        assert error.code == "E001"
        assert error.details == {"detail": "test"}
        assert hasattr(error, 'timestamp')

    def test_configuration_error(self):
        """Test ConfigurationError exception"""
        from anonsuite import ConfigurationError

        error = ConfigurationError("Config error", {"config": "test"})
        assert error.message == "Config error"
        assert error.code == "E001"
        assert error.details == {"config": "test"}

    def test_network_interface_error(self):
        """Test NetworkInterfaceError exception"""
        from anonsuite import NetworkInterfaceError

        error = NetworkInterfaceError("Interface error")
        assert error.message == "Interface error"
        assert error.code == "E002"

class TestUtilityFunctions:
    """Test utility functions"""

    def test_save_output_json(self, tmp_path):
        """Test saving output in JSON format"""
        from anonsuite import _save_output

        test_data = {"test": "data", "number": 123}
        output_file = tmp_path / "test_output.json"

        _save_output(test_data, str(output_file), "json")

        # Verify file was created and contains correct data
        assert output_file.exists()
        with open(output_file) as f:
            loaded_data = json.load(f)
        assert loaded_data == test_data

    def test_save_output_text(self, tmp_path):
        """Test saving output in text format"""
        from anonsuite import _save_output

        test_data = {"test": "data"}
        output_file = tmp_path / "test_output.txt"

        _save_output(test_data, str(output_file), "text")

        # Verify file was created
        assert output_file.exists()
        content = output_file.read_text()
        assert "test" in content
        assert "data" in content

# Integration-style tests for core functionality
class TestCoreIntegration:
    """Test core component integration"""

    @patch('anonsuite.ConfigManager')
    @patch('anonsuite.PluginManager')
    def test_cli_config_integration(self, mock_plugin_manager, mock_config_manager):
        """Test CLI and configuration integration"""
        # Setup mock config
        mock_config = Mock()
        mock_config.get.return_value = True
        mock_config_manager.return_value = mock_config

        cli = AnonSuiteCLI()

        # Test that CLI uses config
        assert cli.config == mock_config

        # Test config access
        cli.config.get.assert_called()

    @patch('anonsuite.ConfigManager')
    @patch('anonsuite.PluginManager')
    def test_cli_plugin_integration(self, mock_plugin_manager, mock_config_manager):
        """Test CLI and plugin system integration"""
        # Setup mock plugin manager
        mock_pm = Mock()
        mock_pm.loaded_plugins = {"test_plugin": Mock()}
        mock_plugin_manager.return_value = mock_pm

        cli = AnonSuiteCLI()

        # Test that CLI uses plugin manager
        assert cli.plugin_manager == mock_pm
        assert "test_plugin" in cli.plugin_manager.loaded_plugins

if __name__ == "__main__":
    pytest.main([__file__])
