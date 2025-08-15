#!/usr/bin/env python3
"""
Enhanced Configuration Manager for AnonSuite
Bulletproof configuration handling with user-friendly error messages
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

class ConfigurationError(Exception):
    """User-friendly configuration errors"""
    def __init__(self, message: str, suggestion: str = None):
        self.message = message
        self.suggestion = suggestion
        super().__init__(self.message)

class ConfigManagerEnhanced:
    """Enhanced configuration manager with bulletproof error handling"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Set up configuration paths
        self.project_root = self._find_project_root()
        self.config_dir = os.path.join(self.project_root, "config")
        self.config_file_path = os.path.join(self.config_dir, "anonsuite.conf")
        self.profiles_dir = os.path.join(self.config_dir, "profiles")
        
        # Default configuration
        self._default_config = self._get_default_config()
        self._current_config = {}
        self._current_profile = "default"
        
        # Initialize configuration
        self._initialize_config()
    
    def _find_project_root(self) -> str:
        """Find AnonSuite project root directory"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Look for project markers
        for _ in range(5):  # Search up to 5 levels up
            if os.path.exists(os.path.join(current_dir, "src", "anonsuite.py")):
                return current_dir
            parent = os.path.dirname(current_dir)
            if parent == current_dir:  # Reached filesystem root
                break
            current_dir = parent
        
        # Fallback to current directory's parent
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration with all required settings"""
        return {
            "general": {
                "version": "2.0.0",
                "debug": False,
                "log_level": "INFO",
                "log_file": os.path.join(self.project_root, "log", "anonsuite.log"),
                "data_dir": os.path.join(self.project_root, "run"),
                "temp_dir": "/tmp/anonsuite"
            },
            "anonymity": {
                "tor": {
                    "socks_port": 9000,
                    "control_port": 9001,
                    "data_directory": os.path.join(self.project_root, "src", "anonymity", "multitor", "tor_9000"),
                    "config_file": os.path.join(self.project_root, "src", "anonymity", "multitor", "tor_9000", "torrc"),
                    "circuit_timeout": 60,
                    "new_circuit_period": 30
                },
                "privoxy": {
                    "listen_port": 8119,
                    "forward_socks5": "127.0.0.1:9000"
                }
            },
            "wifi": {
                "scanner": {
                    "scan_timeout": 30,
                    "max_results": 100,
                    "results_dir": os.path.join(self.project_root, "run", "wifi_scans")
                },
                "pixiewps": {
                    "binary_path": os.path.join(self.project_root, "src", "wifi", "pixiewps", "pixiewps"),
                    "results_dir": os.path.join(self.project_root, "run", "pixiewps_results"),
                    "timeout": 300
                }
            },
            "plugins": {
                "directory": os.path.join(self.project_root, "plugins"),
                "auto_load": True,
                "allowed_imports": ["subprocess", "os", "json", "time", "datetime"]
            },
            "ui": {
                "colors": True,
                "progress_indicators": True,
                "menu_timeout": 300,
                "confirm_dangerous_actions": True
            }
        }
    
    def _initialize_config(self) -> None:
        """Initialize configuration with proper error handling"""
        try:
            # Ensure directories exist
            os.makedirs(self.config_dir, exist_ok=True)
            os.makedirs(self.profiles_dir, exist_ok=True)
            os.makedirs(os.path.dirname(self._default_config["general"]["log_file"]), exist_ok=True)
            os.makedirs(self._default_config["general"]["data_dir"], exist_ok=True)
            
            # Load configuration
            self._load_config()
            
        except Exception as e:
            self.logger.warning(f"Configuration initialization failed: {e}")
            # Use default configuration as fallback
            self._current_config = self._default_config.copy()
    
    def _load_config(self) -> None:
        """Load configuration from file with fallback to defaults"""
        if os.path.exists(self.config_file_path):
            try:
                with open(self.config_file_path, 'r') as f:
                    file_config = json.load(f)
                
                # Merge with defaults (defaults take precedence for missing keys)
                self._current_config = self._merge_configs(self._default_config, file_config)
                
            except json.JSONDecodeError as e:
                raise ConfigurationError(
                    f"Configuration file has invalid JSON format",
                    f"Fix the JSON syntax in {self.config_file_path} or delete it to recreate"
                )
            except Exception as e:
                raise ConfigurationError(
                    f"Cannot read configuration file: {e}",
                    f"Check file permissions for {self.config_file_path}"
                )
        else:
            # Create default configuration file
            self._current_config = self._default_config.copy()
            self.save_config()
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """Recursively merge user config with defaults"""
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'general.version')"""
        try:
            keys = key.split('.')
            value = self._current_config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception:
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self._current_config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
    
    def save_config(self) -> None:
        """Save current configuration to file"""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            
            with open(self.config_file_path, 'w') as f:
                json.dump(self._current_config, f, indent=2)
                
        except Exception as e:
            raise ConfigurationError(
                f"Cannot save configuration: {e}",
                f"Check write permissions for {self.config_dir}"
            )
    
    def validate_config(self) -> Dict[str, List[str]]:
        """Validate configuration and return issues"""
        issues = {"errors": [], "warnings": []}
        
        try:
            # Check required directories
            required_dirs = [
                self.get("general.data_dir"),
                self.get("general.temp_dir"),
                self.get("plugins.directory")
            ]
            
            for dir_path in required_dirs:
                if dir_path and not os.path.exists(dir_path):
                    try:
                        os.makedirs(dir_path, exist_ok=True)
                        issues["warnings"].append(f"Created missing directory: {dir_path}")
                    except Exception:
                        issues["errors"].append(f"Cannot create required directory: {dir_path}")
            
            # Check port ranges
            tor_socks = self.get("anonymity.tor.socks_port", 9000)
            tor_control = self.get("anonymity.tor.control_port", 9001)
            
            if not (1024 <= tor_socks <= 65535):
                issues["errors"].append(f"Tor SOCKS port {tor_socks} is not in valid range (1024-65535)")
            
            if not (1024 <= tor_control <= 65535):
                issues["errors"].append(f"Tor control port {tor_control} is not in valid range (1024-65535)")
            
            if tor_socks == tor_control:
                issues["errors"].append("Tor SOCKS and control ports cannot be the same")
            
            # Check file permissions
            log_file = self.get("general.log_file")
            if log_file:
                log_dir = os.path.dirname(log_file)
                if not os.access(log_dir, os.W_OK):
                    issues["warnings"].append(f"Log directory may not be writable: {log_dir}")
            
        except Exception as e:
            issues["errors"].append(f"Configuration validation failed: {e}")
        
        return issues
    
    def list_profiles(self) -> List[str]:
        """List available configuration profiles"""
        profiles = ["default"]
        
        if os.path.exists(self.profiles_dir):
            for file in os.listdir(self.profiles_dir):
                if file.endswith('.json'):
                    profiles.append(file[:-5])  # Remove .json extension
        
        return profiles
    
    @property
    def current_profile(self) -> str:
        """Get current profile name"""
        return self._current_profile
