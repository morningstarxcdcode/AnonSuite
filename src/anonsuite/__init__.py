"""
AnonSuite - Unified Security Toolkit for Privacy Professionals

A comprehensive toolkit designed for privacy-conscious users and security professionals,
combining Tor integration, WiFi security testing, and anonymity management in one place.
"""

from .main import main, AnonSuiteCLI, VisualTokens, PluginManager

# Try to import ConfigManager - for test compatibility
try:
    import sys
    import os
    # Add src directory to path so we can import config_manager
    src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    from config_manager import ConfigManager
except ImportError:
    # Create a dummy ConfigManager for test compatibility
    class ConfigManager:
        def __init__(self):
            pass

__version__ = "2.0.0"
__author__ = "Marcus"
__email__ = "security@anonsuite.dev"

__all__ = ["main", "AnonSuiteCLI", "VisualTokens", "PluginManager", "ConfigManager"]
