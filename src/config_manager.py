#!/usr/bin/env python3
"""
Configuration Manager - Central Configuration System
Part of AnonSuite Core Infrastructure
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List


class ConfigManager:
    """Centralized configuration management for AnonSuite"""

    def __init__(self, config_dir: str = None):
        self.logger = logging.getLogger(__name__)

        # Set default config directory
        if config_dir is None:
            # Try to find project root from current file location
            current_file = os.path.abspath(__file__)
            project_root = os.path.dirname(os.path.dirname(current_file))  # Go up two levels from src/
            self.config_dir = os.path.join(project_root, "config")
        else:
            self.config_dir = config_dir

        self.config_file = os.path.join(self.config_dir, "anonsuite.conf")
        self.config_file_path = self.config_file  # Alias for compatibility with health check
        self.profiles_dir = os.path.join(self.config_dir, "profiles")
        self.current_profile = "default"

        self._ensure_directories()
        self._load_default_config()

    def _ensure_directories(self):
        """Ensure configuration directories exist"""
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.profiles_dir, exist_ok=True)

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values"""
        # Determine project root dynamically
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(current_file))  # Go up two levels from src/
        
        return {
            "general": {
                "version": "2.0.0",
                "debug": False,
                "log_level": "INFO",

            },
            "anonymity": {
                "tor": {
                    "socks_port": 9000,
                    "control_port": 9001,
                    "data_directory": os.path.join(project_root, "src", "anonymity", "multitor", "tor_9000"),
                    "config_file": os.path.join(project_root, "src", "anonymity", "multitor", "tor_9000", "torrc"),
                    "log_file": os.path.join(project_root, "src", "anonymity", "multitor", "tor_9000", "tor.log"),
                    "circuit_timeout": 60,
                    "new_circuit_period": 30,
                    "max_circuit_dirtiness": 600
                },
                "privoxy": {
                    "listen_port": 8119,

            },
            "wifi": {
                "pixiewps": {
                    "binary_path": os.path.join(project_root, "src", "wifi", "pixiewps", "pixiewps"),
                    "results_dir": os.path.join(project_root, "run", "pixiewps_results"),
                    "timeout": 300,
                    "verbosity": 3
                },
                "wifipumpkin3": {
                    "path": os.path.join(project_root, "src", "wifi", "wifipumpkin3"),
                    "results_dir": os.path.join(project_root, "run", "wifipumpkin_results"),
                    "config_dir": os.path.join(project_root, "config", "wifipumpkin"),
                    "default_ssid": "FreeWiFi",
                    "default_channel": 6,
                    "captive_portal": True
                },
                "scanner": {
                    "results_dir": os.path.join(project_root, "run", "wifi_scans"),
                    "scan_timeout": 30,
                    "max_results": 100
                }
            },
            "security": {
                "bandit": {
                    "config_file": os.path.join(project_root, "config", "bandit.yaml"),
                    "output_format": "json",
                    "severity_level": "low"
                },
                "permissions": {
                    "require_root": False,
                    "check_file_permissions": True,
                    "secure_temp_files": True
                }
            },
            "ui": {
                "colors": True,
                "progress_indicators": True,
                "menu_timeout": 300,
                "confirm_dangerous_actions": True
            },
            "plugins": {
                "directory": os.path.join(project_root, "plugins"),
                "auto_load": True,
                "allowed_imports": ["subprocess", "os", "json", "time", "datetime"]
            }
        }

    def _load_default_config(self):
        """Load or create default configuration"""
        if not os.path.exists(self.config_file):
            self.config = self._get_default_config()
            self.save_config()
        else:
            self.load_config()

    def load_config(self, profile: str = None) -> bool:
        """Load configuration from file"""
        try:
            if profile:
                config_file = os.path.join(self.profiles_dir, f"{profile}.json")
                if not os.path.exists(config_file):
                    self.logger.error(f"Profile '{profile}' not found")
                    return False
            else:
                config_file = self.config_file

            with open(config_file) as f:
                self.config = json.load(f)

            if profile:
                self.current_profile = profile

            self.logger.info(f"Configuration loaded from {config_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self.config = self._get_default_config()
            return False

    def save_config(self, profile: str = None) -> bool:
        """Save current configuration to file"""
        try:
            if profile:
                config_file = os.path.join(self.profiles_dir, f"{profile}.json")
                self.current_profile = profile
            else:
                config_file = self.config_file

            # Add metadata
            config_with_meta = self.config.copy()
            config_with_meta["_metadata"] = {
                "created": datetime.now().isoformat(),
                "profile": profile or "default",
                "version": self.config.get("general", {}).get("version", "2.0.0")
            }

            with open(config_file, 'w') as f:
                json.dump(config_with_meta, f, indent=2)

            self.logger.info(f"Configuration saved to {config_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'tor.socks_port')"""
        try:
            keys = key_path.split('.')
            value = self.config

            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default

            return value

        except Exception:
            return default

    def set(self, key_path: str, value: Any) -> bool:
        """Set configuration value using dot notation"""
        try:
            keys = key_path.split('.')
            config_ref = self.config

            # Navigate to the parent of the target key
            for key in keys[:-1]:
                if key not in config_ref:
                    config_ref[key] = {}
                config_ref = config_ref[key]

            # Set the value
            config_ref[keys[-1]] = value
            return True

        except Exception as e:
            self.logger.error(f"Failed to set config value {key_path}: {e}")
            return False

    def create_profile(self, name: str, base_profile: str = None) -> bool:
        """Create a new configuration profile"""
        try:
            if base_profile and base_profile != "default":
                # Load base profile
                base_config_file = os.path.join(self.profiles_dir, f"{base_profile}.json")
                if os.path.exists(base_config_file):
                    with open(base_config_file) as f:
                        base_config = json.load(f)
                    # Remove metadata
                    if "_metadata" in base_config:
                        del base_config["_metadata"]
                else:
                    base_config = self._get_default_config()
            else:
                base_config = self._get_default_config()

            # Save as new profile
            profile_file = os.path.join(self.profiles_dir, f"{name}.json")

            profile_config = base_config.copy()
            profile_config["_metadata"] = {
                "created": datetime.now().isoformat(),
                "profile": name,
                "base_profile": base_profile or "default",
                "version": self.config.get("general", {}).get("version", "2.0.0")
            }

            with open(profile_file, 'w') as f:
                json.dump(profile_config, f, indent=2)

            self.logger.info(f"Profile '{name}' created")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create profile '{name}': {e}")
            return False

    def list_profiles(self) -> List[str]:
        """List available configuration profiles"""
        profiles = ["default"]

        try:
            if os.path.exists(self.profiles_dir):
                for filename in os.listdir(self.profiles_dir):
                    if filename.endswith('.json'):
                        profile_name = filename[:-5]  # Remove .json extension
                        profiles.append(profile_name)

        except Exception as e:
            self.logger.error(f"Failed to list profiles: {e}")

        return sorted(profiles)

    def delete_profile(self, name: str) -> bool:
        """Delete a configuration profile"""
        if name == "default":
            self.logger.error("Cannot delete default profile")
            return False

        try:
            profile_file = os.path.join(self.profiles_dir, f"{name}.json")
            if os.path.exists(profile_file):
                os.remove(profile_file)
                self.logger.info(f"Profile '{name}' deleted")
                return True
            else:
                self.logger.error(f"Profile '{name}' not found")
                return False

        except Exception as e:
            self.logger.error(f"Failed to delete profile '{name}': {e}")
            return False

    def export_profile(self, name: str, export_path: str) -> bool:
        """Export profile to external file"""
        try:
            if name == "default":
                source_file = self.config_file
            else:
                source_file = os.path.join(self.profiles_dir, f"{name}.json")

            if not os.path.exists(source_file):
                self.logger.error(f"Profile '{name}' not found")
                return False

            # Copy file
            with open(source_file) as src:
                config_data = json.load(src)

            # Add export metadata
            config_data["_export_metadata"] = {
                "exported_at": datetime.now().isoformat(),
                "exported_from": name,
                "anonsuite_version": self.config.get("general", {}).get("version", "2.0.0")
            }

            with open(export_path, 'w') as dst:
                json.dump(config_data, dst, indent=2)

            self.logger.info(f"Profile '{name}' exported to {export_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export profile '{name}': {e}")
            return False

    def import_profile(self, name: str, import_path: str) -> bool:
        """Import profile from external file"""
        try:
            if not os.path.exists(import_path):
                self.logger.error(f"Import file not found: {import_path}")
                return False

            with open(import_path) as f:
                imported_config = json.load(f)

            # Remove export metadata
            if "_export_metadata" in imported_config:
                del imported_config["_export_metadata"]

            # Update metadata
            imported_config["_metadata"] = {
                "created": datetime.now().isoformat(),
                "profile": name,
                "imported_from": import_path,
                "version": self.config.get("general", {}).get("version", "2.0.0")
            }

            # Save as new profile
            profile_file = os.path.join(self.profiles_dir, f"{name}.json")
            with open(profile_file, 'w') as f:
                json.dump(imported_config, f, indent=2)

            self.logger.info(f"Profile '{name}' imported from {import_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to import profile '{name}': {e}")
            return False

    def validate_config(self) -> Dict[str, List[str]]:
        """Validate current configuration"""
        issues = {
            "errors": [],
            "warnings": [],
            "info": []
        }

        # Check required directories
        required_dirs = [
            self.get("general.data_dir"),
            self.get("general.temp_dir"),
            self.get("wifi.pixiewps.results_dir"),
            self.get("wifi.wifipumpkin3.results_dir"),
            self.get("wifi.scanner.results_dir")
        ]

        for dir_path in required_dirs:
            if dir_path and not os.path.exists(dir_path):
                issues["warnings"].append(f"Directory does not exist: {dir_path}")

        # Check binary paths
        binary_paths = [
            self.get("wifi.pixiewps.binary_path")
        ]

        for binary_path in binary_paths:
            if binary_path:
                if not os.path.exists(binary_path):
                    issues["warnings"].append(f"Binary not found (may need compilation): {binary_path}")
                elif not os.access(binary_path, os.X_OK):
                    issues["errors"].append(f"Binary not executable: {binary_path}")

        # Check port conflicts
        ports = [
            self.get("anonymity.tor.socks_port"),
            self.get("anonymity.tor.control_port"),
            self.get("anonymity.privoxy.listen_port")
        ]

        for port in ports:
            if port and (port < 1024 or port > 65535):
                issues["warnings"].append(f"Port out of recommended range: {port}")

        # Check log levels
        log_level = self.get("general.log_level")
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if log_level not in valid_levels:
            issues["errors"].append(f"Invalid log level: {log_level}")

        return issues

    def reset_to_defaults(self) -> bool:
        """Reset configuration to default values"""
        try:
            self.config = self._get_default_config()
            self.save_config()
            self.logger.info("Configuration reset to defaults")
            return True
        except Exception as e:
            self.logger.error(f"Failed to reset configuration: {e}")
            return False


# Test function
def test_config_manager():
    """Test function for configuration manager"""
    config_mgr = ConfigManager()

    print("Testing Configuration Manager...")

    # Test basic operations
    print(f"Tor SOCKS port: {config_mgr.get('anonymity.tor.socks_port')}")
    print(f"WiFi results dir: {config_mgr.get('wifi.scanner.results_dir')}")

    # Test setting values
    config_mgr.set('general.debug', True)
    print(f"Debug mode: {config_mgr.get('general.debug')}")

    # Test profiles
    profiles = config_mgr.list_profiles()
    print(f"Available profiles: {profiles}")

    # Test validation
    issues = config_mgr.validate_config()
    print(f"Config validation - Errors: {len(issues['errors'])}, Warnings: {len(issues['warnings'])}")

    return {"test": "completed", "profiles": len(profiles)}

if __name__ == "__main__":
    test_config_manager()
