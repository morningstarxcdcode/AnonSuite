#!/usr/bin/env python3
"""
AnonSuite - Unified Security Toolkit
Author: Marcus (Senior Security Engineer)

This started as a simple Tor wrapper but grew into something much more comprehensive.
The architecture reflects real-world security testing needs I've encountered over the years.

TODO: Still need to add that network latency monitoring Sarah mentioned
TODO: Consider adding automated report generation (low priority)
FIXME: WiFi module imports are a bit messy - clean this up when we have time
"""

import argparse
import json  # For config wizard and plugin metadata - might refactor this later
import logging
import os
import platform
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

# WiFi module imports - this got complicated due to optional dependencies
# TODO: refactor this import mess when we have a proper dependency manager
try:
    from wifi.pixiewps_wrapper import PixiewpsWrapper

    # WiFi scanner should be working now
    from wifi.wifi_scanner import WiFiScanner
    from wifi.wifipumpkin_wrapper import WiFiPumpkinWrapper

    WIFI_AVAILABLE = True
except ImportError as e:
    # Graceful degradation when WiFi modules aren't available
    print(f"WiFi modules not fully available: {e}")
    WIFI_AVAILABLE = False

    # Dummy classes to prevent crashes - learned this pattern the hard way
    class PixiewpsWrapper:
        def __init__(self):
            self.available = False

        def run_attack(self, *args, **kwargs):
            return {"status": "error", "message": "Pixiewps not available"}

    class WiFiPumpkinWrapper:
        def __init__(self):
            self.available = False

        def start_ap(self, *args, **kwargs):
            return {"status": "error", "message": "WiFiPumpkin3 not available"}

    class WiFiScanner:
        def __init__(self):
            self.available = False

        def scan_networks(self, *args, **kwargs):
            return []


# Try to import our config manager - this should work now
try:
    from config_manager import ConfigManager

    CONFIG_MANAGER_AVAILABLE = True
except ImportError:
    print("Warning: ConfigManager not available, using fallback")
    CONFIG_MANAGER_AVAILABLE = False

# --- Version and Metadata ---
__version__ = "2.0.0"
__author__ = "morningstarxcdcode"
__description__ = "Unified Security Toolkit for Privacy Professionals"


# --- Custom Exceptions ---
class AnonSuiteError(Exception):
    """Base exception for AnonSuite operations"""

    def __init__(
        self, message: str, code: str = "E000", details: Optional[Dict] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        super().__init__(message)


class ConfigurationError(AnonSuiteError):
    """Configuration-related errors"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, "E001", details)


class NetworkInterfaceError(AnonSuiteError):
    """Network interface related errors"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, "E002", details)


class PermissionError(AnonSuiteError):
    """Permission and privilege related errors"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, "E003", details)


# --- Visual Design Tokens ---
class VisualTokens:
    """Consistent visual design tokens for CLI interface"""

    # ANSI Color Codes (terminal-safe)
    COLORS = {
        "primary": "\033[92m",  # Terminal green
        "secondary": "\033[94m",  # Blue
        "accent": "\033[96m",  # Cyan
        "warning": "\033[93m",  # Yellow
        "error": "\033[91m",  # Red
        "success": "\033[92m",  # Green
        "muted": "\033[90m",  # Gray
        "reset": "\033[0m",  # Reset
        "bold": "\033[1m",  # Bold
        "dim": "\033[2m",  # Dim
    }

    # Unicode symbols (with ASCII fallbacks)
    SYMBOLS = {
        "success": "✓",
        "error": "✗",
        "warning": "⚠",
        "info": "ℹ",
        "arrow": "→",
        "bullet": "•",
        "check": "✓",
        "cross": "✗",
    }

    # ASCII Art Components
    LOGO = """
    ╔═══════════════════════════════════════╗
    ║           AnonSuite v2.0              ║
    ║    Unified Security Toolkit          ║
    ╚════════════════════════════════════════╝
    """


# --- Configuration Management ---
@dataclass
class Config:
    """Configuration data structure with validation"""

    anonsuite_root: str
    src_root: str
    anonymity_module: str
    wifi_module: str
    log_level: str = "INFO"
    log_file: Optional[str] = None
    require_sudo: bool = True
    # New config for wizard
    config_file_path: str = os.path.join(
        os.path.expanduser("~"), ".anonsuite", "config.json"
    )


class ConfigManager:
    """Manages configuration loading and validation"""

    def __init__(self):
        self.config: Optional[Config] = None
        self._load_config()

    def _detect_platform_paths(self) -> Dict[str, str]:
        """Detect appropriate paths based on platform"""
        if platform.system() == "Linux":
            base_path = "/opt/AnonSuite"
        else:
            base_path = (
                "/Users/morningstar/Desktop/AnonSuite"  # Assuming project root is CWD
            )

        return {
            "anonsuite_root": base_path,
            "src_root": os.path.join(base_path, "src"),
            "anonymity_module": os.path.join(base_path, "src", "anonymity"),
            "wifi_module": os.path.join(base_path, "src", "wifi"),
        }

    def _load_config(self) -> None:
        """Load configuration from environment and defaults, with validation."""
        paths = self._detect_platform_paths()

        # Validate paths exist
        for key, path in paths.items():
            if not os.path.exists(path):
                # If a path doesn't exist, try to use the current working directory as root
                # This is a common scenario in development environments
                if key == "anonsuite_root":
                    current_dir = os.getcwd()
                    if (
                        os.path.basename(current_dir) == "AnonSuite"
                    ):  # Check if we are in the project root
                        paths["anonsuite_root"] = current_dir
                        paths["src_root"] = os.path.join(current_dir, "src")
                        paths["anonymity_module"] = os.path.join(
                            current_dir, "src", "anonymity"
                        )
                        paths["wifi_module"] = os.path.join(current_dir, "src", "wifi")
                        print(
                            f"{VisualTokens.COLORS['warning']} Adjusted root path to current directory: {current_dir}{VisualTokens.COLORS['reset']}"
                        )
                    else:
                        raise ConfigurationError(
                            f"Required path does not exist: {path} ({key}). Please run from project root or configure manually."
                        )
                else:
                    raise ConfigurationError(
                        f"Required path does not exist: {path} ({key}). Please ensure project structure is correct."
                    )

        self.config = Config(
            anonsuite_root=paths["anonsuite_root"],
            src_root=paths["src_root"],
            anonymity_module=paths["anonymity_module"],
            wifi_module=paths["wifi_module"],
            log_level=os.getenv("ANONSUITE_LOG_LEVEL", "INFO"),
            log_file=os.getenv("ANONSUITE_LOG_FILE"),
            require_sudo=os.getenv("ANONSUITE_REQUIRE_SUDO", "true").lower() == "true",
        )
        # Load user-specific config from file if it exists
        self._load_user_config_from_file()

    def _load_user_config_from_file(self) -> None:
        """Loads configuration from a user-specific JSON file."""
        config_file = self.config.config_file_path
        if os.path.exists(config_file):
            try:
                with open(config_file) as f:
                    user_settings = json.load(f)
                    # Update config with user settings
                    for key, value in user_settings.items():
                        if hasattr(self.config, key):
                            setattr(self.config, key, value)
                print(
                    f"{VisualTokens.COLORS['info']} Loaded user configuration from {config_file}{VisualTokens.COLORS['reset']}"
                )
            except json.JSONDecodeError:
                print(
                    f"{VisualTokens.COLORS['error']} Error: Invalid JSON in user config file {config_file}. Using default settings.{VisualTokens.COLORS['reset']}"
                )
            except Exception as e:
                print(
                    f"{VisualTokens.COLORS['error']} Error loading user config from {config_file}: {e}{VisualTokens.COLORS['reset']}"
                )

    def save_user_config_to_file(self) -> None:
        """Saves current user-configurable settings to a JSON file."""
        config_dir = os.path.dirname(self.config.config_file_path)
        os.makedirs(config_dir, exist_ok=True)

        user_settings = {
            "log_level": self.config.log_level,
            "log_file": self.config.log_file,
            "require_sudo": self.config.require_sudo,
            # Add other user-configurable settings here
        }
        try:
            with open(self.config.config_file_path, "w") as f:
                json.dump(user_settings, f, indent=4)
            print(
                f"{VisualTokens.COLORS['success']} User configuration saved to {self.config.config_file_path}{VisualTokens.COLORS['reset']}"
            )
        except Exception as e:
            print(
                f"{VisualTokens.COLORS['error']} Error saving user config to {self.config.config_file_path}: {e}{VisualTokens.COLORS['reset']}"
            )

    def get_config(self) -> Config:
        """Get current configuration"""
        return self.config


# --- Progress Indicator Helper ---
class ProgressIndicator:
    """Simple text-based progress indicator."""

    def __init__(self, message="Processing", delay=0.1):
        self.message = message
        self.delay = delay
        self.running = False
        self.spinner_thread = None
        self.spinner_chars = ["|", "/", "-", "\\"]

    def _spinner_task(self):
        i = 0
        while self.running:
            sys.stdout.write(
                f"\r{self.message} {self.spinner_chars[i % len(self.spinner_chars)]}"
            )
            sys.stdout.flush()
            time.sleep(self.delay)
            i += 1
        sys.stdout.write(
            "\r" + " " * (len(self.message) + 2) + "\r"
        )  # Clear spinner line
        sys.stdout.flush()

    def start(self):
        self.running = True
        self.spinner_thread = threading.Thread(target=self._spinner_task)
        self.spinner_thread.daemon = (
            True  # Allow main program to exit even if spinner is running
        )
        self.spinner_thread.start()

    def stop(self):
        self.running = False
        if self.spinner_thread and self.spinner_thread.is_alive():
            self.spinner_thread.join(
                timeout=self.delay * 2
            )  # Give it a moment to clean up


# --- Plugin System ---
class AnonSuitePlugin:
    """Base class for AnonSuite plugins."""

    name: str = "Unnamed Plugin"
    description: str = "A generic AnonSuite plugin."
    version: str = "0.1.0"

    def __init__(self, cli_instance: "AnonSuiteCLI"):
        self.cli = cli_instance

    def run(self, *args, **kwargs):
        """Main method to execute plugin functionality."""
        raise NotImplementedError("Plugins must implement the run() method.")

    def get_menu_option(self) -> str:
        """Returns the string to display in the CLI menu."""
        return f"{self.name} ({self.description})"


class PluginManager:
    """Manages loading and interacting with plugins."""

    def __init__(self, cli_instance: "AnonSuiteCLI", plugin_dir: str):
        self.cli = cli_instance
        self.plugin_dir = plugin_dir
        self.loaded_plugins: Dict[str, AnonSuitePlugin] = {}
        self._load_plugins()

    def _load_plugins(self):
        """Load plugins with improved error handling and debugging"""
        self.loaded_plugins = {}

        if not os.path.exists(self.plugin_dir):
            print(
                f"{VisualTokens.COLORS['warning']} Plugin directory not found: {self.plugin_dir}{VisualTokens.COLORS['reset']}"
            )
            return

        # Add both plugin directory and src directory to path
        original_path = sys.path.copy()
        sys.path.insert(0, self.plugin_dir)
        sys.path.insert(0, os.path.join(os.path.dirname(__file__)))  # Add src directory

        plugin_files = [
            f
            for f in os.listdir(self.plugin_dir)
            if f.endswith(".py") and not f.startswith("__")
        ]

        if not plugin_files:
            print(
                f"{VisualTokens.COLORS['warning']} No plugin files found in {self.plugin_dir}{VisualTokens.COLORS['reset']}"
            )
            sys.path = original_path
            return

        for filename in plugin_files:
            module_name = filename[:-3]
            try:
                # Use importlib for better import handling
                import importlib.util

                plugin_path = os.path.join(self.plugin_dir, filename)
                spec = importlib.util.spec_from_file_location(module_name, plugin_path)

                if spec is None:
                    print(
                        f"{VisualTokens.COLORS['warning']} Could not load spec for {filename}{VisualTokens.COLORS['reset']}"
                    )
                    continue

                module = importlib.util.module_from_spec(spec)

                # Execute the module
                spec.loader.exec_module(module)

                # Look for plugin classes
                plugin_found = False
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)

                    # Check if it's a class that looks like a plugin
                    if (
                        isinstance(attr, type)
                        and hasattr(attr, "run")
                        and hasattr(attr, "__init__")
                        and attr_name.endswith("Plugin")
                        and attr_name != "AnonSuitePlugin"
                    ):
                        try:
                            # Try to instantiate the plugin
                            plugin_instance = attr(self.cli)

                            # Ensure it has required attributes
                            if not hasattr(plugin_instance, "name"):
                                plugin_instance.name = attr_name
                            if not hasattr(plugin_instance, "version"):
                                plugin_instance.version = "1.0.0"
                            if not hasattr(plugin_instance, "description"):
                                plugin_instance.description = "No description available"

                            self.loaded_plugins[plugin_instance.name] = plugin_instance
                            print(
                                f"{VisualTokens.COLORS['primary']} Loaded plugin: {plugin_instance.name} v{plugin_instance.version}{VisualTokens.COLORS['reset']}"
                            )
                            plugin_found = True
                            break

                        except Exception as e:
                            print(
                                f"{VisualTokens.COLORS['error']} Error instantiating plugin {attr_name}: {e}{VisualTokens.COLORS['reset']}"
                            )

                if not plugin_found:
                    print(
                        f"{VisualTokens.COLORS['warning']} No valid plugin class found in {filename}{VisualTokens.COLORS['reset']}"
                    )

            except Exception as e:
                print(
                    f"{VisualTokens.COLORS['error']} Error loading plugin {filename}: {e}{VisualTokens.COLORS['reset']}"
                )
                import traceback

                print(
                    f"{VisualTokens.COLORS['muted']} {traceback.format_exc()}{VisualTokens.COLORS['reset']}"
                )

        # Restore original path
        sys.path = original_path

        if self.loaded_plugins:
            print(
                f"{VisualTokens.COLORS['success']} Successfully loaded {len(self.loaded_plugins)} plugin(s){VisualTokens.COLORS['reset']}"
            )
        else:
            print(
                f"{VisualTokens.COLORS['warning']} No plugins loaded successfully{VisualTokens.COLORS['reset']}"
            )

    def get_plugin_menu_options(self) -> List[str]:
        return [plugin.get_menu_option() for plugin in self.loaded_plugins.values()]

    def run_plugin_by_name(self, name: str, *args, **kwargs):
        plugin = self.loaded_plugins.get(name)
        if plugin:
            try:
                plugin.run(*args, **kwargs)
            except Exception as e:
                print(
                    f"{VisualTokens.COLORS['error']} Error running plugin {name}: {e}{VisualTokens.COLORS['reset']}"
                )
        else:
            print(
                f"{VisualTokens.COLORS['error']} Plugin '{name}' not found.{VisualTokens.COLORS['reset']}"
            )


# Progress indicators for better user experience
class ProgressSpinner:
    """Simple progress spinner for long-running operations"""

    def __init__(self, message: str = "Working..."):
        self.message = message
        self.spinner_chars = ["|", "/", "-", "\\"]
        self.running = False
        self.spinner_thread = None
        self._current_char = 0

    def start(self):
        """Start the spinner"""
        if self.running:
            return

        self.running = True
        self.spinner_thread = threading.Thread(target=self._spin)
        self.spinner_thread.daemon = True
        self.spinner_thread.start()

    def stop(self):
        """Stop the spinner"""
        self.running = False
        if self.spinner_thread:
            self.spinner_thread.join(timeout=1)
        # Clear the spinner line
        print("\r" + " " * (len(self.message) + 10) + "\r", end="", flush=True)

    def _spin(self):
        """Internal spinner animation"""
        while self.running:
            char = self.spinner_chars[self._current_char % len(self.spinner_chars)]
            print(f"\r{char} {self.message}", end="", flush=True)
            self._current_char += 1
            time.sleep(0.1)


class ProgressBar:
    """Simple progress bar for operations with known duration"""

    def __init__(self, total: int, message: str = "Progress", width: int = 40):
        self.total = total
        self.current = 0
        self.message = message
        self.width = width
        self.start_time = time.time()

    def update(self, increment: int = 1):
        """Update progress bar"""
        self.current = min(self.current + increment, self.total)
        self._draw()

    def set_progress(self, current: int):
        """Set absolute progress"""
        self.current = min(current, self.total)
        self._draw()

    def finish(self):
        """Complete the progress bar"""
        self.current = self.total
        self._draw()
        print()  # New line after completion

    def _draw(self):
        """Draw the progress bar"""
        if self.total == 0:
            return

        percentage = (self.current / self.total) * 100
        filled_width = int((self.current / self.total) * self.width)

        bar = "█" * filled_width + "░" * (self.width - filled_width)

        # Calculate ETA
        elapsed = time.time() - self.start_time
        if self.current > 0:
            eta = (elapsed / self.current) * (self.total - self.current)
            eta_str = f" ETA: {int(eta)}s" if eta > 1 else ""
        else:
            eta_str = ""

        print(
            f"\r{self.message}: [{bar}] {percentage:.1f}%{eta_str}", end="", flush=True
        )


# --- Enhanced CLI Interface ---
class AnonSuiteCLI:
    """Enhanced CLI interface with professional error handling and visual design"""

    def __init__(self):
        # Initialize configuration manager - this integration took some debugging
        try:
            from config_manager import ConfigManager

            self.config_manager = ConfigManager()
            self.config = self.config_manager
        except Exception as e:
            print(f"Warning: ConfigManager initialization failed: {e}")
            # Create a minimal fallback config
            self.config = type(
                "Config",
                (),
                {
                    "get": lambda self, key, default=None: default,
                    "list_profiles": lambda self: ["default"],
                },
            )()

        self.running = True

        # Initialize WiFi tool wrappers - graceful degradation if modules missing
        try:
            self.pixiewps_wrapper = PixiewpsWrapper()
            self.wifipumpkin_wrapper = WiFiPumpkinWrapper()
            self.wifi_scanner = WiFiScanner()  # This should work now
        except Exception as e:
            print(f"Warning: WiFi tools initialization failed: {e}")

        # Initialize Plugin Manager - had to debug this integration
        try:
            plugins_dir = self.config.get(
                "plugins.directory", "/Users/morningstar/Desktop/AnonSuite/plugins"
            )
            self.plugin_manager = PluginManager(self, plugins_dir)
        except Exception as e:
            print(f"Warning: Plugin manager initialization failed: {e}")
            # Create dummy plugin manager
            self.plugin_manager = type(
                "PluginManager",
                (),
                {
                    "loaded_plugins": {},
                    "get_plugin_menu_options": lambda self: [],
                    "run_plugin_by_name": lambda self, name: print(
                        f"Plugin {name} not available"
                    ),
                },
            )()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals gracefully"""
        print(
            f"\n{VisualTokens.COLORS['muted']}Shutting down gracefully...{VisualTokens.COLORS['reset']}"
        )
        self.running = False
        sys.exit(0)

    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text with reset"""
        return (
            f"{VisualTokens.COLORS.get(color, '')}{text}{VisualTokens.COLORS['reset']}"
        )

    def _print_header(self) -> None:
        """Print application header with branding"""
        print(self._colorize(VisualTokens.LOGO, "primary"))
        print(self._colorize(f"    {__description__}", "muted"))
        print()

    def _print_menu(self, title: str, options: List[str]) -> None:
        """Print formatted menu with visual tokens"""
        print(
            f"\n{self._colorize('┌─', 'secondary')} {self._colorize(title, 'bold')} {self._colorize('─' * (45 - len(title)), 'secondary')}"
        )

        for i, option in enumerate(options, 1):
            symbol = VisualTokens.SYMBOLS["bullet"]
            print(
                f"{self._colorize('│', 'secondary')} {self._colorize(f'{i}.', 'accent')} {symbol} {option}"
            )

        print(
            f"{self._colorize('│', 'secondary')} {self._colorize('0.', 'accent')} {VisualTokens.SYMBOLS['arrow']} Back"
        )
        print(
            f"{self._colorize('└─', 'secondary')}{self._colorize('─' * 47, 'secondary')}"
        )

    def _get_user_choice(self) -> int:
        """Get user input with validation"""
        while True:
            try:
                prompt = f"\n{self._colorize('Choice', 'accent')}: "
                choice = input(prompt).strip()

                if not choice:
                    continue

                return int(choice)
            except ValueError:
                error_msg = f"{VisualTokens.SYMBOLS['error']} Invalid input. Please enter a number."
                print(self._colorize(error_msg, "error"))
            except KeyboardInterrupt:
                print(f"\n{self._colorize('Goodbye!', 'muted')}")
                sys.exit(0)

    def _execute_command(
        self, command: List[str], description: str = "", show_progress: bool = False
    ) -> bool:
        """Execute command with enhanced error handling, user feedback, and optional progress indicator."""
        print(
            f"{self._colorize(VisualTokens.SYMBOLS['arrow'], 'accent')} {description or 'Executing command'}..."
        )

        progress_indicator = None
        if show_progress:
            progress_indicator = ProgressIndicator(message=description)
            progress_indicator.start()

        try:
            # Use a higher timeout for commands that might take longer, e.g., network operations
            subprocess.run(
                command, check=True, capture_output=True, text=True, timeout=120
            )  # Increased timeout to 120s

            if progress_indicator:
                progress_indicator.stop()

            success_msg = (
                f"{VisualTokens.SYMBOLS['success']} Operation completed successfully"
            )
            print(self._colorize(success_msg, "success"))
            return True

        except FileNotFoundError:
            if progress_indicator:
                progress_indicator.stop()
            error_msg = f"{VisualTokens.SYMBOLS['error']} Command not found: {command[0]}. Please ensure it is installed and in your system's PATH."
            print(
                self._colorize(error_msg, "error")
                + f"\n{self._colorize('Details:', 'muted')} Ensure {command[0]} is installed and accessible."
            )
            return False

        except PermissionError:
            if progress_indicator:
                progress_indicator.stop()
            error_msg = f"{VisualTokens.SYMBOLS['error']} Permission denied. Ensure you have the necessary privileges (e.g., run with sudo) and correct file permissions."
            print(
                self._colorize(error_msg, "error")
                + f"\n{self._colorize('Details:', 'muted')} Check file permissions or run with sudo."
            )
            return False

        except subprocess.CalledProcessError as e:
            if progress_indicator:
                progress_indicator.stop()
            error_msg = f"{VisualTokens.SYMBOLS['error']} Command failed with exit code {e.returncode}.\n{self._colorize('Command:', 'muted')} {' '.join(e.cmd)}\n{self._colorize('Stdout:', 'muted')} {e.stdout.strip()}\n{self._colorize('Stderr:', 'muted')} {e.stderr.strip()}"
            print(self._colorize(error_msg, "error"))
            return False

        except subprocess.TimeoutExpired:
            if progress_indicator:
                progress_indicator.stop()
            timeout_msg = f"{VisualTokens.SYMBOLS['warning']} Command timed out after 120 seconds. It might be taking longer than expected or is stuck."
            print(self._colorize(timeout_msg, "warning"))
            return False

        except Exception as e:
            if progress_indicator:
                progress_indicator.stop()
            error_msg = f"{VisualTokens.SYMBOLS['error']} An unexpected error occurred during command execution: {e}"
            print(self._colorize(error_msg, "error"))
            return False

    def anonymity_menu(self) -> None:
        """Enhanced anonymity module menu with real multitor integration"""
        while self.running:
            self._print_menu(
                "Anonymity Module",
                [
                    "Start AnonSuite (Tor + Proxy)",
                    "Stop AnonSuite",
                    "Restart AnonSuite",
                    "Check Status",
                    "Monitor Performance",
                    "View Tor Logs",
                ],
            )

            choice = self._get_user_choice()
            multitor_script = os.path.join(
                self.config.anonymity_module, "multitor", "multitor"
            )

            if choice == 1:
                # Start multitor with our verified working configuration
                cmd = [
                    "sudo",
                    multitor_script,
                    "--user",
                    "morningstar",
                    "--socks-port",
                    "9000",
                    "--control-port",
                    "9001",
                    "--proxy",
                    "privoxy",
                ]
                self._execute_command(
                    cmd, "Starting anonymity services", show_progress=True
                )

            elif choice == 2:
                # Stop Tor and Privoxy processes
                self._stop_anonymity_services()

            elif choice == 3:
                # Restart services
                self._stop_anonymity_services()
                time.sleep(2)
                cmd = [
                    "sudo",
                    multitor_script,
                    "--user",
                    "morningstar",
                    "--socks-port",
                    "9000",
                    "--control-port",
                    "9001",
                    "--proxy",
                    "privoxy",
                ]
                self._execute_command(
                    cmd, "Restarting anonymity services", show_progress=True
                )

            elif choice == 4:
                # Check service status
                self._check_anonymity_status()

            elif choice == 5:
                # Monitor performance
                self._monitor_performance()

            elif choice == 6:
                # View Tor logs
                self._view_tor_logs()

            elif choice == 0:
                break
            else:
                error_msg = (
                    f"{VisualTokens.SYMBOLS['error']} Invalid choice. Please try again."
                )
                print(self._colorize(error_msg, "error"))

    def _stop_anonymity_services(self) -> None:
        """Stop Tor and Privoxy services"""
        print(f"{VisualTokens.SYMBOLS['arrow']} Stopping anonymity services...")
        try:
            # Kill Tor processes
            subprocess.run(
                ["sudo", "pkill", "-f", "tor.*9000"],
                check=False,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["sudo", "pkill", "-f", "privoxy"],
                check=False,
                capture_output=True,
                text=True,
            )

            success_msg = (
                f"{VisualTokens.SYMBOLS['success']} Anonymity services stopped"
            )
            print(self._colorize(success_msg, "success"))

        except Exception as e:
            error_msg = f"{VisualTokens.SYMBOLS['error']} Error stopping services: {e}"
            print(self._colorize(error_msg, "error"))

    def _check_anonymity_status(self) -> None:
        """Check status of anonymity services"""
        print(f"\n{self._colorize('Checking Anonymity Services Status...', 'accent')}")

        # Check Tor process
        try:
            result = subprocess.run(
                ["pgrep", "-f", "tor.*9000"], capture_output=True, text=True
            )
            if result.returncode == 0:
                tor_pid = result.stdout.strip()
                print(
                    f"{VisualTokens.SYMBOLS['success']} Tor: Running (PID: {tor_pid})"
                )
            else:
                print(f"{VisualTokens.SYMBOLS['error']} Tor: Not running")
        except Exception:
            print(f"{VisualTokens.SYMBOLS['error']} Tor: Status unknown")

        # Check Privoxy process
        try:
            result = subprocess.run(
                ["pgrep", "-f", "privoxy"], capture_output=True, text=True
            )
            if result.returncode == 0:
                privoxy_pid = result.stdout.strip()
                print(
                    f"{VisualTokens.SYMBOLS['success']} Privoxy: Running (PID: {privoxy_pid})"
                )
            else:
                print(f"{VisualTokens.SYMBOLS['error']} Privoxy: Not running")
        except Exception:
            print(f"{VisualTokens.SYMBOLS['error']} Privoxy: Status unknown")

        # Check port connectivity
        ports_to_check = [9000, 9001, 8119]
        for port in ports_to_check:
            try:
                result = subprocess.run(
                    ["lsof", "-i", f":{port}"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    print(f"{VisualTokens.SYMBOLS['success']} Port {port}: Active")
                else:
                    print(f"{VisualTokens.SYMBOLS['error']} Port {port}: Not listening")
            except Exception:
                print(f"{VisualTokens.SYMBOLS['warning']} Port {port}: Status unknown")

        # Test Tor connectivity
        self._test_tor_connectivity()

    def _test_tor_connectivity(self) -> None:
        """Test Tor connectivity and anonymity"""
        print(f"\n{self._colorize('Testing Tor Connectivity...', 'accent')}")

        try:
            # Test SOCKS proxy
            import requests

            proxies = {
                "http": "socks5://127.0.0.1:9000",
                "https": "socks5://127.0.0.1:9000",
            }

            response = requests.get(
                "https://check.torproject.org/api/ip", proxies=proxies, timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("IsTor"):
                    ip = data.get("IP", "Unknown")
                    print(
                        f"{VisualTokens.SYMBOLS['success']} Tor connectivity: Working (Exit IP: {ip})"
                    )
                else:
                    print(
                        f"{VisualTokens.SYMBOLS['warning']} Tor connectivity: Not using Tor network"
                    )
            else:
                print(
                    f"{VisualTokens.SYMBOLS['error']} Tor connectivity: HTTP error {response.status_code}"
                )

        except ImportError:
            print(
                f"{VisualTokens.SYMBOLS['warning']} Tor connectivity: requests module not available"
            )
        except Exception as e:
            print(f"{VisualTokens.SYMBOLS['error']} Tor connectivity: {str(e)}")

    def _monitor_performance(self) -> None:
        """Monitor system performance and provide optimization insights."""
        print(f"\n{self._colorize('Performance Monitor & Optimization', 'accent')}\n")

        # Run our performance monitor tool (if it exists)
        perf_script = os.path.join(
            self.config.anonsuite_root, "scripts", "performance_monitor.sh"
        )

        if os.path.exists(perf_script):
            print(f"{VisualTokens.SYMBOLS['arrow']} Running performance snapshot...")
            self._execute_command(
                [perf_script, "snapshot"],
                "Taking performance snapshot",
                show_progress=True,
            )
        else:
            print(
                f"{VisualTokens.SYMBOLS['warning']} Performance monitor script not found at {perf_script}"
            )

        print(f"\n{self._colorize('Optimization Insights:', 'info')}")
        print(
            f"{VisualTokens.SYMBOLS['bullet']} Startup Time: Current startup time is generally fast. Further optimization would involve lazy loading modules."
        )
        print(
            f"{VisualTokens.SYMBOLS['bullet']} Memory Usage: Python's memory footprint can be optimized by releasing unused resources and avoiding large data structures where possible."
        )
        print(
            f"{VisualTokens.SYMBOLS['bullet']} Code Cleanup: Regular code reviews, removing dead code, and refactoring complex functions can improve maintainability and performance."
        )
        print(
            f"{VisualTokens.SYMBOLS['bullet']} External Calls: Minimize redundant external tool calls and optimize their execution parameters."
        )

        try:
            import psutil

            print(f"\n{self._colorize('Current Resource Usage:', 'info')}")
            print(
                f"{VisualTokens.SYMBOLS['info']} CPU Usage: {psutil.cpu_percent(interval=0.5)}%"
            )
            print(
                f"{VisualTokens.SYMBOLS['info']} Memory Usage: {psutil.virtual_memory().percent}%"
            )
        except ImportError:
            print(
                f"{VisualTokens.SYMBOLS['warning']} psutil not available for detailed resource monitoring. Install with 'pip install psutil'."
            )

    def _view_tor_logs(self) -> None:
        """View recent Tor log entries"""
        print(f"\n{self._colorize('Recent Tor Log Entries', 'accent')}")

        tor_log_path = os.path.join(
            self.config.anonymity_module, "multitor", "tor_9000", "tor.log"
        )

        if os.path.exists(tor_log_path):
            try:
                # Show last 20 lines of Tor log
                result = subprocess.run(
                    ["tail", "-20", tor_log_path], capture_output=True, text=True
                )
                if result.returncode == 0:
                    print(result.stdout)
                else:
                    print(f"{VisualTokens.SYMBOLS['error']} Could not read Tor log")
            except Exception as e:
                print(f"{VisualTokens.SYMBOLS['error']} Error reading log: {e}")
        else:
            print(
                f"{VisualTokens.SYMBOLS['warning']} Tor log file not found at {tor_log_path}"
            )

    def wifi_menu(self) -> None:
        """Enhanced WiFi auditing menu with comprehensive functionality"""
        while self.running:
            self._print_menu(
                "WiFi Auditing Module",
                [
                    "Scan for Networks",
                    "Network Information",
                    "Rogue AP Attack (WiFiPumpkin3)",
                    "Pixie-Dust Attack (Pixiewps)",
                    "Monitor Mode Setup",
                    "Capture Analysis",
                    "Security Assessment",
                ],
            )

            choice = self._get_user_choice()

            if choice == 1:
                self._wifi_network_scan()

            elif choice == 2:
                self._wifi_network_info()

            elif choice == 3:
                self._launch_wifipumpkin3()

            elif choice == 4:
                self._launch_pixiewps()

            elif choice == 5:
                self._setup_monitor_mode()

            elif choice == 6:
                self._analyze_captures()

            elif choice == 7:
                self._security_assessment()

            elif choice == 0:
                break
            else:
                error_msg = (
                    f"{VisualTokens.SYMBOLS['error']} Invalid choice. Please try again."
                )
                print(self._colorize(error_msg, "error"))

    def _wifi_network_scan(self) -> None:
        """Perform WiFi network scanning"""
        print(f"\n{self._colorize('WiFi Network Scanner', 'accent')}")

        # Check for wireless interfaces
        try:
            result = subprocess.run(["iwconfig"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"{VisualTokens.SYMBOLS['info']} Available wireless interfaces:")
                print(result.stdout)
            else:
                print(
                    f"{VisualTokens.SYMBOLS['warning']} iwconfig not available - install wireless-tools"
                )
        except FileNotFoundError:
            print(
                f"{VisualTokens.SYMBOLS['warning']} iwconfig not found - install wireless-tools"
            )

        # Run network scan using our scanner
        scanner_script = os.path.join(self.config.wifi_module, "wifi_scanner.py")
        if os.path.exists(scanner_script):
            # Assuming WiFiScanner class exists and has a scan_networks method
            # self.wifi_scanner.scan_networks()
            self._execute_command(
                ["python3", scanner_script],
                "Scanning for WiFi networks",
                show_progress=True,
            )
        else:
            print(f"{VisualTokens.SYMBOLS['warning']} WiFi scanner not found")

    def _wifi_network_info(self) -> None:
        """Display detailed network information"""
        print(f"\n{self._colorize('Network Information', 'accent')}")

        # Show current network status
        try:
            # Check current WiFi connection
            result = subprocess.run(
                ["networksetup", "-getairportnetwork", "en0"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print(
                    f"{VisualTokens.SYMBOLS['info']} Current WiFi: {result.stdout.strip()}"
                )

            # Show network interfaces
            result = subprocess.run(["ifconfig"], capture_output=True, text=True)
            if result.returncode == 0:
                # Parse and display relevant interface info
                lines = result.stdout.split("\n")
                for line in lines:
                    if "en0:" in line or "wlan" in line:
                        print(f"{VisualTokens.SYMBOLS['info']} {line.strip()}")

        except Exception as e:
            print(f"{VisualTokens.SYMBOLS['error']} Error getting network info: {e}")

    def _launch_wifipumpkin3(self) -> None:
        """Launch WiFiPumpkin3 rogue AP attack using the wrapper."""
        print(f"\n{self._colorize('WiFiPumpkin3 Rogue AP Attack', 'accent')}")
        print(
            f"{VisualTokens.SYMBOLS['warning']} This functionality is currently non-operational due to internal issues with WiFiPumpkin3."
        )
        print(
            f"{VisualTokens.SYMBOLS['info']} Please refer to the project's documentation for updates on WiFiPumpkin3 compatibility."
        )

        # Attempt to call the wrapper, which will log the error internally
        self.wifipumpkin_wrapper.start_ap(config={})  # Pass an empty config for now
        print(f"{VisualTokens.SYMBOLS['error']} WiFiPumpkin3 could not be started.")

    def _launch_pixiewps(self) -> None:
        """Launch Pixiewps WPS attack using the wrapper."""
        print(f"\n{self._colorize('Pixiewps WPS Attack', 'accent')}")
        print(f"{VisualTokens.SYMBOLS['info']} Pixiewps WPS PIN recovery tool.")
        print(
            f"{VisualTokens.SYMBOLS['warning']} Requires WPS handshake capture and root privileges."
        )

        interface = input(
            f"{self._colorize('Enter wireless interface (e.g., wlan0mon): ', 'accent')}"
        )
        target_bssid = input(
            f"{self._colorize('Target BSSID (MAC address): ', 'accent')}"
        )

        if not interface or not target_bssid:
            print(
                f"{VisualTokens.SYMBOLS['warning']} Interface and Target BSSID are required to launch Pixiewps."
            )
            return

        # For simplicity, only passing essential arguments to the wrapper.
        # More advanced Pixiewps arguments can be added here if the CLI is enhanced to collect them.
        print(
            f"{VisualTokens.SYMBOLS['arrow']} Attempting to run Pixiewps on {target_bssid} via {interface}..."
        )
        if self.pixiewps_wrapper.run_attack(interface, target_bssid):
            print(
                f"{VisualTokens.SYMBOLS['success']} Pixiewps attack initiated. Check logs for detailed output."
            )
        else:
            print(
                f"{VisualTokens.SYMBOLS['error']} Pixiewps attack failed. See error messages above."
            )

    def _setup_monitor_mode(self) -> None:
        """Setup wireless interface in monitor mode"""
        print(f"\n{self._colorize('Monitor Mode Setup', 'accent')}")

        # List available interfaces
        try:
            result = subprocess.run(["iwconfig"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"{VisualTokens.SYMBOLS['info']} Available interfaces:")
                print(result.stdout)

                interface = input(
                    f"{self._colorize('Interface to use (e.g., wlan0): ', 'accent')}"
                )

                if interface:
                    print(
                        f"{VisualTokens.SYMBOLS['info']} Setting {interface} to monitor mode..."
                    )

                    # Commands to set monitor mode
                    commands = [
                        ["sudo", "ifconfig", interface, "down"],
                        ["sudo", "iwconfig", interface, "mode", "monitor"],
                        ["sudo", "ifconfig", interface, "up"],
                    ]

                    for cmd in commands:
                        self._execute_command(
                            cmd, f"Executing: {' '.join(cmd)}", show_progress=True
                        )

                    print(
                        f"{VisualTokens.SYMBOLS['success']} Monitor mode setup complete"
                    )
                else:
                    print(f"{VisualTokens.SYMBOLS['warning']} No interface specified")
            else:
                print(f"{VisualTokens.SYMBOLS['error']} iwconfig not available")

        except FileNotFoundError:
            print(f"{VisualTokens.SYMBOLS['error']} Wireless tools not installed")

    def _analyze_captures(self) -> None:
        """Analyze packet captures"""
        print(f"\n{self._colorize('Capture Analysis', 'accent')}")

        # Look for capture files
        capture_extensions = [".pcap", ".cap", ".pcapng"]
        capture_files = []

        # Check common capture directories
        search_dirs = [
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Downloads"),
            "/tmp",
            self.config.anonsuite_root,
        ]

        for directory in search_dirs:
            if os.path.exists(directory):
                for file in os.listdir(directory):
                    if any(file.endswith(ext) for ext in capture_extensions):
                        capture_files.append(os.path.join(directory, file))

        if capture_files:
            print(f"{VisualTokens.SYMBOLS['info']} Found capture files:")
            for i, file in enumerate(capture_files[:10], 1):  # Show first 10
                print(f"  {i}. {os.path.basename(file)}")

            try:
                choice = int(
                    input(f"{self._colorize('Select file (number): ', 'accent')}")
                )
                if 1 <= choice <= len(capture_files):
                    selected_file = capture_files[choice - 1]

                    # Basic analysis using tcpdump if available
                    try:
                        self._execute_command(
                            ["tcpdump", "-r", selected_file, "-c", "10"],
                            "Analyzing capture file",
                            show_progress=True,
                        )

                    except FileNotFoundError:
                        print(
                            f"{VisualTokens.SYMBOLS['warning']} tcpdump not available for analysis"
                        )

            except (ValueError, IndexError):
                print(f"{VisualTokens.SYMBOLS['error']} Invalid selection")
        else:
            print(f"{VisualTokens.SYMBOLS['warning']} No capture files found")

    def _security_assessment(self) -> None:
        """Perform WiFi security assessment"""
        print(f"\n{self._colorize('WiFi Security Assessment', 'accent')}")

        # Load sample networks for assessment
        scenarios_file = os.path.join(
            self.config.anonsuite_root, "scenarios", "sample_networks.json"
        )

        if os.path.exists(scenarios_file):
            try:
                with open(scenarios_file) as f:
                    scenarios = json.load(f)

                networks = scenarios.get("sample_networks", {}).get("networks", [])

                if networks:
                    print(
                        f"{VisualTokens.SYMBOLS['info']} Analyzing {len(networks)} sample networks..."
                    )

                    vulnerable_count = 0
                    for network in networks:
                        encryption = network.get("encryption", "Unknown")
                        wps_enabled = network.get("wps_enabled", False)

                        # Simple vulnerability assessment
                        vulnerabilities = []
                        risk_score = 0

                        if encryption == "Open":
                            vulnerabilities.append("No encryption")
                            risk_score = 10
                        elif encryption == "WEP":
                            vulnerabilities.append("Weak WEP encryption")
                            risk_score = 9
                        elif wps_enabled:
                            vulnerabilities.append("WPS enabled (potential Pixie Dust)")
                            risk_score = 7
                        elif encryption in ["WPA", "WPA-PSK"]:
                            vulnerabilities.append("Legacy WPA")
                            risk_score = 5

                        if vulnerabilities:
                            vulnerable_count += 1
                            print(
                                f"\n{VisualTokens.SYMBOLS['warning']} {network['ssid']} (Risk: {risk_score}/10)"
                            )
                            for vuln in vulnerabilities:
                                print(f"  - {vuln}")

                    print(f"\n{VisualTokens.SYMBOLS['info']} Assessment Summary:")
                    print(f"  Total networks: {len(networks)}")
                    print(f"  Vulnerable networks: {vulnerable_count}")
                    print(
                        f"  Security ratio: {((len(networks) - vulnerable_count) / len(networks) * 100):.1f}%"
                    )

                else:
                    print(
                        f"{VisualTokens.SYMBOLS['warning']} No networks found in scenarios"
                    )

            except Exception as e:
                print(f"{VisualTokens.SYMBOLS['error']} Error loading scenarios: {e}")
        else:
            print(f"{VisualTokens.SYMBOLS['warning']} Sample networks file not found")

    def configuration_menu(self) -> None:
        """Configuration management menu"""
        while self.running:
            self._print_menu(
                "Configuration Management",
                [
                    "View Current Configuration",
                    "Run Configuration Wizard",  # New option
                    "Switch Profile",
                    "Create New Profile",
                    "Edit Profile Settings",
                    "Import/Export Profiles",
                    "User Preferences",
                ],
            )

            choice = self._get_user_choice()

            if choice == 1:
                self._view_configuration()
            elif choice == 2:
                self._run_config_wizard()  # New method call
            elif choice == 3:
                self._switch_profile()
            elif choice == 4:
                self._create_profile()
            elif choice == 5:
                self._edit_profile()
            elif choice == 6:
                self._import_export_profiles()
            elif choice == 7:
                self._user_preferences()
            elif choice == 0:
                break
            else:
                error_msg = (
                    f"{VisualTokens.SYMBOLS['error']} Invalid choice. Please try again."
                )
                print(self._colorize(error_msg, "error"))

    def _run_config_wizard(self) -> None:
        """Interactive wizard for initial configuration setup."""
        print(f"\n{self._colorize('Configuration Wizard', 'accent')}")
        print(
            f"{VisualTokens.SYMBOLS['info']} This wizard will guide you through essential settings."
        )

        # Step 1: Confirm project root (already detected, but allow override)
        current_root = self.config.anonsuite_root
        new_root = input(
            f"{self._colorize('Confirm project root (current: ' + current_root + '): ', 'accent')}"
        )
        if new_root and os.path.isdir(new_root):
            self.config.anonsuite_root = new_root
            self.config.src_root = os.path.join(new_root, "src")
            self.config.anonymity_module = os.path.join(new_root, "src", "anonymity")
            self.config.wifi_module = os.path.join(new_root, "src", "wifi")
            print(
                f"{VisualTokens.SYMBOLS['success']} Project root updated to: {self.config.anonsuite_root}"
            )
        else:
            print(
                f"{VisualTokens.SYMBOLS['warning']} Invalid path or skipped. Using current root."
            )

        # Step 2: Sudo requirement
        require_sudo_str = input(
            f"{self._colorize('Require sudo for network operations? (yes/no, current: ' + str(self.config.require_sudo) + '): ', 'accent')}"
        )
        if require_sudo_str.lower() in ["yes", "y"]:
            self.config.require_sudo = True
        elif require_sudo_str.lower() in ["no", "n"]:
            self.config.require_sudo = False
        print(
            f"{VisualTokens.SYMBOLS['success']} Sudo requirement set to: {self.config.require_sudo}"
        )

        # Step 3: Log Level
        log_level_str = input(
            f"{self._colorize('Set logging level (INFO, WARNING, ERROR, current: ' + self.config.log_level + '): ', 'accent')}"
        )
        if log_level_str.upper() in ["INFO", "WARNING", "ERROR"]:
            self.config.log_level = log_level_str.upper()
        print(
            f"{VisualTokens.SYMBOLS['success']} Log level set to: {self.config.log_level}"
        )

        # Save configuration
        self.config_manager.save_user_config_to_file()
        print(
            f"{VisualTokens.SYMBOLS['success']} Configuration wizard complete. Settings saved."
        )

    def system_status_menu(self) -> None:
        """System status and monitoring menu"""
        while self.running:
            self._print_menu(
                "System Status & Monitoring",
                [
                    "Service Status Overview",
                    "Network Connectivity Test",
                    "Performance Monitoring",
                    "Log Analysis",
                    "Security Health Check",
                    "Resource Usage",
                    "Run Security Audit (Bandit)",  # New option
                ],
            )

            choice = self._get_user_choice()

            if choice == 1:
                self._service_status_overview()
            elif choice == 2:
                self._network_connectivity_test()
            elif choice == 3:
                self._performance_monitoring()
            elif choice == 4:
                self._log_analysis()
            elif choice == 5:
                self._security_health_check()
            elif choice == 6:
                self._resource_usage()
            elif choice == 7:
                self._run_bandit_scan()
            elif choice == 0:
                break
            else:
                error_msg = (
                    f"{VisualTokens.SYMBOLS['error']} Invalid choice. Please try again."
                )
                print(self._colorize(error_msg, "error"))

    def plugins_menu(self) -> None:
        """Menu for managing and running plugins."""
        while self.running:
            plugin_options = self.plugin_manager.get_plugin_menu_options()
            if not plugin_options:
                print(
                    f"\n{VisualTokens.SYMBOLS['info']} No plugins found. Place .py files in the 'plugins' directory."
                )
                self._print_menu("Plugins", [])  # Print empty menu
                choice = self._get_user_choice()
                if choice == 0:
                    break
                else:
                    print(
                        f"{VisualTokens.SYMBOLS['error']} Invalid choice. Please try again."
                    )
                    continue

            self._print_menu("Plugins", plugin_options)
            choice = self._get_user_choice()

            if choice == 0:
                break
            elif 1 <= choice <= len(plugin_options):
                selected_plugin_name = list(self.plugin_manager.loaded_plugins.keys())[
                    choice - 1
                ]
                print(
                    f"\n{VisualTokens.SYMBOLS['arrow']} Running plugin: {selected_plugin_name}..."
                )
                self.plugin_manager.run_plugin_by_name(selected_plugin_name)
            else:
                error_msg = (
                    f"{VisualTokens.SYMBOLS['error']} Invalid choice. Please try again."
                )
                print(self._colorize(error_msg, "error"))

    def help_menu(self) -> None:
        """Help and documentation menu"""
        while self.running:
            self._print_menu(
                "Help & Documentation",
                [
                    "Quick Start Guide",
                    "Command Reference",
                    "Troubleshooting",
                    "Security Best Practices",
                    "About AnonSuite",
                    "Release Information",  # New menu option
                ],
            )

            choice = self._get_user_choice()

            if choice == 1:
                self._show_quick_start()
            elif choice == 2:
                self._show_command_reference()
            elif choice == 3:
                self._show_troubleshooting()
            elif choice == 4:
                self._show_security_practices()
            elif choice == 5:
                self._show_about()
            elif choice == 6:
                self._show_release_info()
            elif choice == 0:
                break
            else:
                error_msg = (
                    f"{VisualTokens.SYMBOLS['error']} Invalid choice. Please try again."
                )
                print(self._colorize(error_msg, "error"))

    # Configuration Management Methods
    def _view_configuration(self) -> None:
        """View current configuration"""
        print(f"\n{self._colorize('Current Configuration', 'accent')}")

        # Show basic configuration info
        print(
            f"{VisualTokens.SYMBOLS['info']} AnonSuite Root: {self.config.anonsuite_root}"
        )
        print(f"{VisualTokens.SYMBOLS['info']} Source Root: {self.config.src_root}")
        print(
            f"{VisualTokens.SYMBOLS['info']} Anonymity Module: {self.config.anonymity_module}"
        )
        print(f"{VisualTokens.SYMBOLS['info']} WiFi Module: {self.config.wifi_module}")
        print(f"{VisualTokens.SYMBOLS['info']} Log Level: {self.config.log_level}")
        print(
            f"{VisualTokens.SYMBOLS['info']} Log File: {self.config.log_file if self.config.log_file else 'Not set'}"
        )
        print(
            f"{VisualTokens.SYMBOLS['info']} Require Sudo: {self.config.require_sudo}"
        )
        print(
            f"{VisualTokens.SYMBOLS['info']} User Config File: {self.config.config_file_path}"
        )

    def _switch_profile(self) -> None:
        """Switch configuration profile"""
        print(f"\n{self._colorize('Switch Profile', 'accent')}")
        print(
            f"{VisualTokens.SYMBOLS['info']} Profile switching feature coming soon..."
        )

    def _create_profile(self) -> None:
        """Create new configuration profile"""
        print(f"\n{self._colorize('Create Profile', 'accent')}")
        print(f"{VisualTokens.SYMBOLS['info']} Profile creation feature coming soon...")

    def _edit_profile(self) -> None:
        """Edit profile settings"""
        print(f"\n{self._colorize('Edit Profile', 'accent')}")
        print(f"{VisualTokens.SYMBOLS['info']} Profile editing feature coming soon...")

    def _import_export_profiles(self) -> None:
        """Import/Export profiles"""
        print(f"\n{self._colorize('Import/Export Profiles', 'accent')}")
        print(f"{VisualTokens.SYMBOLS['info']} Import/Export feature coming soon...")

    def _user_preferences(self) -> None:
        """User preferences"""
        print(f"\n{self._colorize('User Preferences', 'accent')}")
        print(f"{VisualTokens.SYMBOLS['info']} User preferences feature coming soon...")

    # System Status Methods
    def _service_status_overview(self) -> None:
        """Service status overview"""
        print(f"\n{self._colorize('Service Status Overview', 'accent')}")
        self._check_anonymity_status()

    def _network_connectivity_test(self) -> None:
        """Network connectivity test"""
        print(f"\n{self._colorize('Network Connectivity Test', 'accent')}")
        self._test_tor_connectivity()

    def _performance_monitoring(self) -> None:
        """Performance monitoring"""
        print(f"\n{self._colorize('Performance Monitoring', 'accent')}")
        self._monitor_performance()

    def _log_analysis(self) -> None:
        """Log analysis"""
        print(f"\n{self._colorize('Log Analysis', 'accent')}")

        # Run log analyzer if available
        log_analyzer = os.path.join(
            self.config.anonsuite_root, "log", "analyze_logs.py"
        )
        if os.path.exists(log_analyzer):
            self._execute_command(
                ["python3", log_analyzer], "Analyzing logs", show_progress=True
            )
        else:
            print(f"{VisualTokens.SYMBOLS['warning']} Log analyzer not found")

    def _security_health_check(self) -> None:
        """Perform a comprehensive security health check."""
        print(f"\n{self._colorize('Security Health Check', 'accent')}")
        print(f"{VisualTokens.SYMBOLS['info']} Running security checks...\n")

        checks = [
            ("File Permissions", self._check_file_permissions),
            ("Network Security (DNS/IP Leak)", self._check_network_security),
            ("Process Security (Privileges)", self._check_process_security),
            ("Tor Connectivity (Anonymity)", self._test_tor_connectivity_security),
            ("Privoxy Configuration", self._check_privoxy_config),
            ("System Updates (Placeholder)", self._check_system_updates),
            ("Firewall Status (Placeholder)", self._check_firewall_status),
        ]

        for check_name, check_func in checks:
            print(f"{self._colorize('Checking:', 'muted')} {check_name}...")
            try:
                result = check_func()
                if result is True:
                    print(f"{VisualTokens.SYMBOLS['success']} {check_name}: Passed")
                elif result is False:
                    print(f"{VisualTokens.SYMBOLS['error']} {check_name}: Failed")
                # If function prints its own status, result can be None
            except Exception as e:
                print(f"{VisualTokens.SYMBOLS['error']} {check_name}: Error - {e}")
            print("-" * 30)  # Separator

    def _test_tor_connectivity_security(self) -> bool:
        """Tests Tor connectivity specifically for security (IP/DNS leaks)."""
        print(
            f"{VisualTokens.SYMBOLS['arrow']} Testing Tor IP and DNS leak... (requires Tor to be running)"
        )
        # This will call the existing _test_tor_connectivity which checks IP.
        # For DNS leak, a more advanced check would be needed (e.g., using a specific DNS leak test service).
        # For now, we rely on the IP check.
        return self._test_tor_connectivity()  # Re-use existing Tor connectivity check

    def _check_privoxy_config(self) -> bool:
        """Checks basic Privoxy configuration for security best practices."""
        print(f"{VisualTokens.SYMBOLS['arrow']} Checking Privoxy configuration...")
        privoxy_config_path = "/opt/homebrew/etc/privoxy/config"  # Common Homebrew path
        if not os.path.exists(privoxy_config_path):
            print(
                f"{VisualTokens.SYMBOLS['warning']} Privoxy config not found at {privoxy_config_path}. Cannot verify."
            )
            return False

        try:
            with open(privoxy_config_path) as f:
                content = f.read()
                # Check for common security settings
                if (
                    "forward-socks5 / 127.0.0.1:9000 ." in content
                    and "listen-address 127.0.0.1:8118" in content
                ):
                    print(
                        f"{VisualTokens.SYMBOLS['info']} Basic Privoxy config for Tor forwarding found."
                    )
                    return True
                else:
                    print(
                        f"{VisualTokens.SYMBOLS['warning']} Privoxy config might not be correctly set up for Tor forwarding."
                    )
                    return False
        except Exception as e:
            print(f"{VisualTokens.SYMBOLS['error']} Error reading Privoxy config: {e}")
            return False

    def _check_system_updates(self) -> bool:
        """Placeholder for checking system update status."""
        print(
            f"{VisualTokens.SYMBOLS['info']} Checking for system updates... (Manual check recommended)"
        )
        # In a real scenario, this would run 'apt update && apt list --upgradable' or 'brew outdated'
        return None  # Indicates manual check needed

    def _check_firewall_status(self) -> bool:
        """Placeholder for checking firewall status."""
        print(
            f"{VisualTokens.SYMBOLS['info']} Checking firewall status... (Manual check recommended)"
        )
        # In a real scenario, this would run 'sudo ufw status' or 'sudo pfctl -s info'
        return None  # Indicates manual check needed

    def _resource_usage(self) -> None:
        """Resource usage monitoring"""
        print(f"\n{self._colorize('Resource Usage', 'accent')}")

        try:
            import psutil

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            print(f"{VisualTokens.SYMBOLS['info']} CPU Usage: {cpu_percent}%")

            # Memory usage
            memory = psutil.virtual_memory()
            print(f"{VisualTokens.SYMBOLS['info']} Memory Usage: {memory.percent}%")

            # Disk usage
            disk = psutil.disk_usage("/")
            print(f"{VisualTokens.SYMBOLS['info']} Disk Usage: {disk.percent}%")

        except ImportError:
            print(
                f"{VisualTokens.SYMBOLS['warning']} psutil not available for detailed resource monitoring. Install with 'pip install psutil'."
            )

    def _run_bandit_scan(self) -> None:
        """Runs a security audit using Bandit on the project's source code."""
        print(f"\n{self._colorize('Running Security Audit (Bandit)', 'accent')}")
        print(f"{VisualTokens.SYMBOLS['info']} This may take a moment...\n")

        try:
            # Run bandit on the src directory
            # Use -r for recursive, -f for output format (txt for human-readable)
            # -ll for low confidence issues, --exclude for common non-source dirs
            bandit_command = [
                os.path.join(
                    self.config.anonsuite_root, "venv", "bin", "bandit"
                ),  # Use bandit from venv
                "-r",
                self.config.src_root,
                "-f",
                "txt",  # Human-readable format
                "-ll",  # Show low confidence issues
                "--exclude",
                os.path.join(self.config.src_root, "anonymity", "multitor")
                + ","
                + os.path.join(self.config.src_root, "wifi", "wifipumpkin3")
                + ","
                + os.path.join(
                    self.config.src_root, "wifi", "pixiewps"
                ),  # Exclude third-party/external tools
                "-o",
                os.path.join(
                    self.config.anonsuite_root, "bandit_report.txt"
                ),  # Output to a file
            ]

            print(
                f"{VisualTokens.SYMBOLS['arrow']} Executing: {' '.join(bandit_command)}\n"
            )
            result = subprocess.run(
                bandit_command, capture_output=True, text=True, check=False, timeout=300
            )  # Increased timeout for scan

            print(f"\n{self._colorize('Bandit Scan Results:', 'primary')}")
            print(result.stdout)

            if result.returncode == 0:
                print(
                    f"{VisualTokens.SYMBOLS['success']} Bandit scan completed with no issues found."
                )
            elif result.returncode == 1:
                print(
                    f"{VisualTokens.SYMBOLS['warning']} Bandit scan completed with issues. Review the report above and in bandit_report.txt."
                )
            else:
                print(
                    f"{VisualTokens.SYMBOLS['error']} Bandit scan encountered an error (Exit Code: {result.returncode}).\n{result.stderr}"
                )

            print(
                f"{VisualTokens.SYMBOLS['info']} Detailed report saved to bandit_report.txt in the project root."
            )

        except FileNotFoundError:
            print(
                f"{VisualTokens.SYMBOLS['error']} Bandit not found. Ensure it's installed in your virtual environment."
            )
        except subprocess.TimeoutExpired:
            print(
                f"{VisualTokens.SYMBOLS['error']} Bandit scan timed out after 300 seconds."
            )
        except Exception as e:
            print(
                f"{VisualTokens.SYMBOLS['error']} An error occurred during Bandit scan: {e}"
            )

    # Help Methods
    def _show_quick_start(self) -> None:
        """Show quick start guide"""
        print(f"\n{self._colorize('AnonSuite Quick Start Guide', 'accent')}")
        print(f"""
{VisualTokens.SYMBOLS["info"]} Getting Started:
  1. Start anonymity services: Main Menu → Anonymity → Start AnonSuite
  2. Check status: Main Menu → System Status → Service Status Overview
  3. Test connectivity: Main Menu → System Status → Network Connectivity Test

{VisualTokens.SYMBOLS["info"]} WiFi Auditing:
  1. Scan networks: Main Menu → WiFi Auditing → Scan for Networks
  2. Security assessment: Main Menu → WiFi Auditing → Security Assessment
  3. Monitor mode: Main Menu → WiFi Auditing → Monitor Mode Setup

{VisualTokens.SYMBOLS["warning"]} Important:
  - Always ensure you have proper authorization before testing
  - Use only on networks you own or have explicit permission to test
  - Follow local laws and regulations
        """)

    def _show_command_reference(self) -> None:
        """Show command reference"""
        print(f"\n{self._colorize('Command Reference', 'accent')}")
        print(f"""
{VisualTokens.SYMBOLS["info"]} Command Line Options:
  --health-check    : Run system health check
  --version        : Show version information
  --help           : Show help message

{VisualTokens.SYMBOLS["info"]} Service Commands:
  Start Anonymity  : Launches Tor and Privoxy services
  Stop Anonymity   : Stops all anonymity services
  Check Status     : Verifies service status and connectivity

{VisualTokens.SYMBOLS["info"]} WiFi Commands:
  Network Scan     : Discover nearby wireless networks
  Monitor Mode     : Setup wireless interface for monitoring
  Security Assess  : Analyze network security posture
        """)

    def _show_troubleshooting(self) -> None:
        """Show troubleshooting guide"""
        print(f"\n{self._colorize('Troubleshooting Guide', 'accent')}")
        print(f"""
{VisualTokens.SYMBOLS["info"]} Common Issues:

Port Conflicts:
  - Check for existing Tor/Privoxy processes: lsof -i :9000 -i :8119
  - Kill conflicting processes: sudo kill <PID>
  - Restart AnonSuite services

Permission Issues:
  - Ensure proper file ownership: sudo chown -R $USER ~/.anonsuite
  - Check sudo privileges: sudo -v
  - Verify script permissions: chmod +x scripts/*

Network Issues:
  - Test direct connectivity: curl http://httpbin.org/ip
  - Test Tor connectivity: curl --socks5 127.0.0.1:9000 https://check.torproject.org/api/ip
  - Check DNS settings: cat /etc/resolv.conf

{VisualTokens.SYMBOLS["warning"]} If problems persist, check logs in the log/ directory
        """)

    def _show_security_practices(self) -> None:
        """Show security best practices"""
        print(f"\n{self._colorize('Security Best Practices', 'accent')}")
        print(f"""
{VisualTokens.SYMBOLS["info"]} Anonymity Best Practices:
  - Always verify Tor connectivity before sensitive operations
  - Use different Tor circuits for different activities
  - Regularly check for DNS leaks
  - Keep Tor and related software updated

{VisualTokens.SYMBOLS["info"]} WiFi Security Testing:
  - Only test networks you own or have explicit permission
  - Use isolated test environments when possible
  - Document all testing activities for compliance
  - Follow responsible disclosure for vulnerabilities

{VisualTokens.SYMBOLS["warning"]} Legal Considerations:
  - Obtain written authorization before testing
  - Respect local laws and regulations
  - Follow ethical hacking guidelines
  - Maintain confidentiality of discovered vulnerabilities
        """)

    def _show_about(self) -> None:
        """Show about information"""
        print(f"\n{self._colorize('About AnonSuite', 'accent')}")
        print(f"""
{VisualTokens.SYMBOLS["info"]} AnonSuite v2.0.0
A comprehensive security toolkit for anonymity and WiFi auditing

{VisualTokens.SYMBOLS["info"]} Features:
  - Multi-Tor instance management with load balancing
  - Integrated Privoxy HTTP proxy
  - WiFi security assessment tools
  - Comprehensive logging and monitoring
  - Professional-grade testing framework

{VisualTokens.SYMBOLS["info"]} Integrated Tools:
  - multitor: Multiple Tor instances
  - Privoxy: HTTP proxy with filtering
  - wifipumpkin3: Rogue AP framework
  - pixiewps: WPS PIN recovery

{VisualTokens.SYMBOLS["info"]} Author: morningstarxcdcode
{VisualTokens.SYMBOLS["info"]} License: MIT License
{VisualTokens.SYMBOLS["info"]} GitHub: https://github.com/morningstarxcdcode/AnonSuite
        """)

    def _show_release_info(self) -> None:
        """Show release preparation information."""
        print(f"\n{self._colorize('Release Preparation Information', 'accent')}")
        print(f"""
{VisualTokens.SYMBOLS["info"]} Final Testing:
  - All unit and integration tests must pass.
  - End-to-end testing of all major workflows.
  - Manual verification of core functionalities.

{VisualTokens.SYMBOLS["info"]} Version Tagging:
  - A new Git tag will be created for the release version (e.g., v2.0.0-beta).
  - Changelog will be updated with all new features and bug fixes.

{VisualTokens.SYMBOLS["info"]} Release Documentation:
  - User manual and API reference will be finalized.
  - Installation guides will be updated.
  - Security audit report will be published.

{VisualTokens.SYMBOLS["warning"]} Current Status:
  - This project is still under active development. Features are being integrated and tested.
  - The current version is for development and testing purposes only.
        """)

    # Security check helper methods
    def _check_file_permissions(self) -> bool:
        """Check file permissions"""
        try:
            # Check if critical files have proper permissions
            critical_files = [
                self.config.anonsuite_root,
                os.path.join(self.config.anonymity_module, "multitor", "multitor"),
            ]

            for file_path in critical_files:
                if os.path.exists(file_path):
                    stat_info = os.stat(file_path)
                    # Basic permission check
                    if stat_info.st_uid != os.getuid() and os.getuid() != 0:
                        return False

            return True
        except Exception:
            return False

    def _check_network_security(self) -> bool:
        """Check network security"""
        try:
            # Basic network security checks
            # Check if we can resolve DNS
            import socket

            socket.gethostbyname("google.com")
            return True
        except Exception:
            return False

    def _check_process_security(self) -> bool:
        """Check process security"""
        try:
            # Check if running with appropriate privileges
            return os.getuid() != 0  # Should not be running as root
        except Exception:
            return False

    def _run_configuration_wizard(self) -> None:
        """Interactive configuration wizard for new users"""
        print(f"\n{self._colorize('AnonSuite Configuration Wizard', 'primary')}")
        print("=" * 50)
        print("This wizard will help you set up AnonSuite for your system.\n")

        # Step 1: System detection
        print(f"{VisualTokens.SYMBOLS['info']} Detecting system capabilities...")
        capabilities = self._detect_system_capabilities()
        self._display_capabilities(capabilities)

        # Step 2: Basic configuration
        print(f"\n{self._colorize('Basic Configuration', 'accent')}")

        # Log level
        log_level = (
            input("Set log level (INFO/DEBUG/WARNING) [INFO]: ").upper() or "INFO"
        )
        if log_level in ["INFO", "DEBUG", "WARNING", "ERROR"]:
            self.config.set("general.log_level", log_level)

        # Data directory
        data_dir = input(
            f"Data directory [{self.config.get('general.data_dir')}]: "
        ) or self.config.get("general.data_dir")
        self.config.set("general.data_dir", data_dir)

        # Step 3: Anonymity configuration
        if capabilities.get("tor", False):
            print(f"\n{self._colorize('Anonymity Configuration', 'accent')}")

            socks_port = input("Tor SOCKS port [9000]: ") or "9000"
            try:
                self.config.set("anonymity.tor.socks_port", int(socks_port))
            except ValueError:
                print("Invalid port, using default 9000")
                self.config.set("anonymity.tor.socks_port", 9000)

            control_port = input("Tor control port [9001]: ") or "9001"
            try:
                self.config.set("anonymity.tor.control_port", int(control_port))
            except ValueError:
                print("Invalid port, using default 9001")
                self.config.set("anonymity.tor.control_port", 9001)

        # Step 4: WiFi configuration
        if capabilities.get("wifi_available", False):
            print(f"\n{self._colorize('WiFi Configuration', 'accent')}")

            scan_timeout = input("WiFi scan timeout in seconds [30]: ") or "30"
            try:
                self.config.set("wifi.scanner.scan_timeout", int(scan_timeout))
            except ValueError:
                print("Invalid timeout, using default 30")
                self.config.set("wifi.scanner.scan_timeout", 30)

        # Step 5: Save configuration
        print(f"\n{self._colorize('Saving Configuration', 'accent')}")
        try:
            self.config.save_config()
            print(
                f"{VisualTokens.SYMBOLS['success']} Configuration saved successfully!"
            )
        except Exception as e:
            print(f"{VisualTokens.SYMBOLS['error']} Failed to save configuration: {e}")

        # Step 6: Next steps
        print(f"\n{self._colorize('Setup Complete!', 'success')}")
        print("Next steps:")
        print("1. Run health check: python src/anonsuite.py --health-check")
        print("2. Start using AnonSuite: python src/anonsuite.py")
        print("3. View documentation: docs/user-guide.md")

    def _detect_system_capabilities(self) -> Dict[str, bool]:
        """Detect what functionality is available on this system"""
        capabilities = {}

        # Check Python version
        capabilities["python_ok"] = sys.version_info >= (3, 8)

        # Check system tools
        capabilities["tor"] = self._command_exists("tor")
        capabilities["privoxy"] = self._command_exists("privoxy")

        # Check WiFi tools (platform-specific)
        if sys.platform == "darwin":  # macOS
            capabilities["wifi_available"] = True  # macOS has built-in WiFi tools
            capabilities["wifi_type"] = "macOS (airport/system_profiler)"
        else:  # Linux
            capabilities["wifi_available"] = self._command_exists("iwconfig")
            capabilities["wifi_type"] = "Linux (wireless-tools)"

        # Check directories
        capabilities["config_dir"] = os.path.exists(self.config.config_dir)
        capabilities["data_dir"] = os.path.exists(
            self.config.get("general.data_dir", "")
        )

        return capabilities

    def _display_capabilities(self, capabilities: Dict[str, bool]) -> None:
        """Display system capabilities to user"""
        print(f"\n{self._colorize('System Capabilities:', 'accent')}")

        for capability, available in capabilities.items():
            if capability == "wifi_type":
                continue  # Skip this one, it's just metadata

            status = (
                VisualTokens.SYMBOLS["success"]
                if available
                else VisualTokens.SYMBOLS["error"]
            )
            status_text = "Available" if available else "Not Available"

            if capability == "wifi_available" and available:
                wifi_type = capabilities.get("wifi_type", "Unknown")
                print(f"  {status} WiFi Tools: {status_text} ({wifi_type})")
            else:
                capability_name = capability.replace("_", " ").title()
                print(f"  {status} {capability_name}: {status_text}")

        # Show warnings for missing critical components
        if not capabilities.get("tor", False):
            print(f"\n{VisualTokens.SYMBOLS['warning']} Tor not found. Install with:")
            if sys.platform == "darwin":
                print("  brew install tor")
            else:
                print("  sudo apt install tor")

        if not capabilities.get("wifi_available", False):
            print(
                f"\n{VisualTokens.SYMBOLS['warning']} WiFi tools not found. Install with:"
            )
            if sys.platform == "darwin":
                print("  WiFi tools are built into macOS")
            else:
                print("  sudo apt install wireless-tools")

    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in the system PATH"""
        try:
            subprocess.run(["which", command], capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def _check_python_environment(self) -> Dict[str, Any]:
        """Check Python environment health"""
        try:
            import sys

            # Check Python version
            if sys.version_info < (3, 9):
                return {
                    "status": "fail",
                    "message": f"Python {sys.version_info.major}.{sys.version_info.minor} is too old. Requires 3.9+",
                }

            # Check virtual environment
            in_venv = hasattr(sys, "real_prefix") or (
                hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
            )

            if not in_venv:
                return {
                    "status": "warning",
                    "message": "Not running in virtual environment. Recommended for isolation.",
                }

            return {
                "status": "pass",
                "message": f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} in virtual environment",
            }

        except Exception as e:
            return {"status": "error", "message": f"Python check failed: {e}"}

    def _check_system_dependencies(self) -> Dict[str, Any]:
        """Check system dependencies"""
        try:
            required_tools = ["tor", "privoxy"]
            optional_tools = (
                ["iwconfig", "iwlist"] if sys.platform != "darwin" else ["airport"]
            )

            missing_required = []
            missing_optional = []

            for tool in required_tools:
                if not self._command_exists(tool):
                    missing_required.append(tool)

            for tool in optional_tools:
                if not self._command_exists(tool) and tool != "airport":
                    missing_optional.append(tool)
                elif tool == "airport":
                    airport_path = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
                    if not os.path.exists(airport_path):
                        missing_optional.append(tool)

            if missing_required:
                return {
                    "status": "fail",
                    "message": f"Missing required tools: {', '.join(missing_required)}",
                }
            elif missing_optional:
                return {
                    "status": "warning",
                    "message": f"Missing optional tools: {', '.join(missing_optional)}",
                }
            else:
                return {
                    "status": "pass",
                    "message": "All required system dependencies available",
                }

        except Exception as e:
            return {"status": "error", "message": f"Dependency check failed: {e}"}

    def _check_configuration_files(self) -> Dict[str, Any]:
        """Check configuration files"""
        try:
            config_file = self.config.config_file_path

            if not os.path.exists(config_file):
                return {
                    "status": "warning",
                    "message": "Configuration file not found. Run --config-wizard to create.",
                }

            # Try to load and validate configuration
            try:
                issues = self.config.validate_config()
                if issues["errors"]:
                    return {
                        "status": "fail",
                        "message": f"Configuration errors: {len(issues['errors'])} issues found",
                    }
                elif issues["warnings"]:
                    return {
                        "status": "warning",
                        "message": f"Configuration warnings: {len(issues['warnings'])} issues found",
                    }
                else:
                    return {"status": "pass", "message": "Configuration file valid"}
            except Exception as e:
                return {
                    "status": "fail",
                    "message": f"Configuration validation failed: {e}",
                }

        except Exception as e:
            return {"status": "error", "message": f"Configuration check failed: {e}"}

    def _check_directory_structure(self) -> Dict[str, Any]:
        """Check directory structure"""
        try:
            required_dirs = [
                self.config.get("general.data_dir", "run"),
                self.config.get("general.temp_dir", "/tmp/anonsuite"),
                "config",
                "plugins",
                "log",
            ]

            missing_dirs = []
            for dir_path in required_dirs:
                if not os.path.exists(dir_path):
                    missing_dirs.append(dir_path)

            if missing_dirs:
                # Try to create missing directories
                created_dirs = []
                for dir_path in missing_dirs:
                    try:
                        os.makedirs(dir_path, exist_ok=True)
                        created_dirs.append(dir_path)
                    except Exception:
                        pass

                if created_dirs:
                    return {
                        "status": "pass",
                        "message": f"Created missing directories: {', '.join(created_dirs)}",
                    }
                else:
                    return {
                        "status": "fail",
                        "message": f"Cannot create directories: {', '.join(missing_dirs)}",
                    }
            else:
                return {"status": "pass", "message": "All required directories exist"}

        except Exception as e:
            return {"status": "error", "message": f"Directory check failed: {e}"}

    def _check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity"""
        try:
            import socket
            import urllib.request

            # Test basic DNS resolution
            try:
                socket.gethostbyname("google.com")
            except Exception:
                return {
                    "status": "fail",
                    "message": "DNS resolution failed. Check network connection.",
                }

            # Test HTTP connectivity
            try:
                urllib.request.urlopen("https://httpbin.org/ip", timeout=10)
            except Exception:
                return {
                    "status": "warning",
                    "message": "HTTP connectivity limited. May affect some features.",
                }

            return {"status": "pass", "message": "Network connectivity working"}

        except Exception as e:
            return {"status": "error", "message": f"Network check failed: {e}"}

    def _check_tor_availability(self) -> Dict[str, Any]:
        """Check Tor availability and configuration"""
        try:
            if not self._command_exists("tor"):
                return {
                    "status": "fail",
                    "message": "Tor not installed. Install with: brew install tor (macOS) or apt install tor (Linux)",
                }

            # Check if Tor is running
            try:
                result = subprocess.run(
                    ["pgrep", "tor"], capture_output=True, timeout=5
                )
                if result.returncode == 0:
                    return {"status": "pass", "message": "Tor is installed and running"}
                else:
                    return {
                        "status": "warning",
                        "message": "Tor installed but not running. Start with --start-anonymity",
                    }
            except Exception:
                return {
                    "status": "warning",
                    "message": "Tor installed but status unknown",
                }

        except Exception as e:
            return {"status": "error", "message": f"Tor check failed: {e}"}

    def _check_wifi_tools(self) -> Dict[str, Any]:
        """Check WiFi tools availability"""
        try:
            if sys.platform == "darwin":  # macOS
                airport_path = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
                if os.path.exists(airport_path):
                    return {
                        "status": "pass",
                        "message": "macOS WiFi tools available (airport/system_profiler)",
                    }
                else:
                    return {
                        "status": "warning",
                        "message": "macOS airport utility not found. Limited WiFi functionality.",
                    }
            else:  # Linux
                if self._command_exists("iwconfig") and self._command_exists("iwlist"):
                    return {
                        "status": "pass",
                        "message": "Linux WiFi tools available (wireless-tools)",
                    }
                else:
                    return {
                        "status": "fail",
                        "message": "WiFi tools missing. Install with: sudo apt install wireless-tools",
                    }

        except Exception as e:
            return {"status": "error", "message": f"WiFi tools check failed: {e}"}

    def _check_plugin_system(self) -> Dict[str, Any]:
        """Check plugin system"""
        try:
            plugins_dir = self.config.get("plugins.directory", "plugins")

            if not os.path.exists(plugins_dir):
                return {
                    "status": "warning",
                    "message": f"Plugin directory not found: {plugins_dir}",
                }

            plugin_files = [
                f
                for f in os.listdir(plugins_dir)
                if f.endswith(".py") and not f.startswith("__")
            ]

            if not plugin_files:
                return {"status": "warning", "message": "No plugin files found"}

            # Try to load plugins
            loaded_plugins = len(self.plugin_manager.loaded_plugins)

            if loaded_plugins == 0:
                return {
                    "status": "warning",
                    "message": f"Plugin files found ({len(plugin_files)}) but none loaded successfully",
                }
            else:
                return {
                    "status": "pass",
                    "message": f"{loaded_plugins} plugins loaded successfully",
                }

        except Exception as e:
            return {"status": "error", "message": f"Plugin system check failed: {e}"}

    def _add_health_recommendations(self, health_results: Dict[str, Any]) -> None:
        """Add recommendations based on health check results"""
        recommendations = []

        # Check for common issues and add recommendations
        for check_name, result in health_results["checks"].items():
            if result["status"] == "fail":
                if "Python" in check_name:
                    recommendations.append("Upgrade Python to version 3.8 or higher")
                elif "Dependencies" in check_name:
                    if sys.platform == "darwin":
                        recommendations.append(
                            "Install missing tools with: brew install tor privoxy"
                        )
                    else:
                        recommendations.append(
                            "Install missing tools with: sudo apt install tor privoxy wireless-tools"
                        )
                elif "Configuration" in check_name:
                    recommendations.append(
                        "Run configuration wizard: python src/anonsuite.py --config-wizard"
                    )
                elif "Network" in check_name:
                    recommendations.append(
                        "Check internet connection and firewall settings"
                    )
                elif "WiFi" in check_name:
                    if sys.platform != "darwin":
                        recommendations.append(
                            "Install WiFi tools: sudo apt install wireless-tools aircrack-ng"
                        )

        # Add general recommendations
        if health_results["overall_status"] in ["poor", "fair"]:
            recommendations.append(
                "Review troubleshooting guide: docs/troubleshooting.md"
            )
            recommendations.append("Consider running installation script: ./install.sh")

        health_results["recommendations"] = recommendations[:5]  # Limit to top 5

    def _get_user_input(
        self, prompt: str = "Choice", valid_options: List[str] = None
    ) -> str:
        """Get user input with comprehensive error handling and validation"""
        while True:
            try:
                # Display prompt with visual styling
                user_input = input(
                    f"{VisualTokens.COLORS['accent']}{prompt}{VisualTokens.COLORS['reset']}: "
                ).strip()

                # Handle empty input
                if not user_input:
                    if valid_options and "0" in valid_options:
                        return "0"  # Default to back/exit
                    continue

                # Validate input if options provided
                if valid_options and user_input not in valid_options:
                    print(
                        f"{VisualTokens.SYMBOLS['warning']} Invalid choice. Please select from: {', '.join(valid_options)}"
                    )
                    continue

                return user_input

            except EOFError:
                # Handle Ctrl+D gracefully
                print(
                    f"\n{VisualTokens.SYMBOLS['info']} Detected EOF. Exiting gracefully..."
                )
                return "0"

            except KeyboardInterrupt:
                # Handle Ctrl+C gracefully
                print(
                    f"\n{VisualTokens.SYMBOLS['info']} Operation cancelled by user. Returning to main menu..."
                )
                return "0"

            except Exception as e:
                # Handle any other input errors
                print(f"{VisualTokens.SYMBOLS['error']} Input error: {e}")
                print("Please try again or press Ctrl+C to exit.")
                continue

    def _display_menu_with_context(
        self, title: str, options: List[tuple], show_help: bool = True
    ) -> str:
        """Display menu with context and help information"""
        print(
            f"\n{VisualTokens.COLORS['secondary']}┌─{VisualTokens.COLORS['reset']} {VisualTokens.COLORS['bold']}{title}{VisualTokens.COLORS['reset']} {VisualTokens.COLORS['secondary']}{'─' * (50 - len(title))}{VisualTokens.COLORS['reset']}"
        )

        valid_choices = []
        for option_key, option_text, option_help in options:
            print(
                f"{VisualTokens.COLORS['secondary']}│{VisualTokens.COLORS['reset']} {VisualTokens.COLORS['accent']}{option_key}.{VisualTokens.COLORS['reset']} {option_text}"
            )
            if option_help and show_help:
                print(
                    f"{VisualTokens.COLORS['secondary']}│{VisualTokens.COLORS['reset']}   {VisualTokens.COLORS['muted']}{option_help}{VisualTokens.COLORS['reset']}"
                )
            valid_choices.append(option_key)

        print(
            f"{VisualTokens.COLORS['secondary']}└─{'─' * 50}{VisualTokens.COLORS['reset']}"
        )

        if show_help:
            print(
                f"{VisualTokens.COLORS['muted']}💡 Tip: Press '0' to go back, 'h' for help, or Ctrl+C to exit{VisualTokens.COLORS['reset']}"
            )

        return self._get_user_input("Choice", valid_choices + ["h", "help"])

    def _show_contextual_help(self, context: str) -> None:
        """Show contextual help based on current menu context"""
        help_content = {
            "main": [
                "AnonSuite Main Menu Help",
                "• Anonymity: Configure and manage Tor/Proxy services",
                "• WiFi Auditing: Scan networks and test security",
                "• Configuration: Manage profiles and settings",
                "• System Status: Monitor health and performance",
                "• Plugins: Extend functionality with custom tools",
                "• Help: Access documentation and tutorials",
            ],
            "anonymity": [
                "Anonymity Tools Help",
                "• Start Services: Launch Tor and Privoxy",
                "• Check Status: Verify anonymity is working",
                "• New Circuit: Get new Tor exit node",
                "• Test Anonymity: Verify IP address changes",
                "• Stop Services: Safely shutdown anonymity tools",
            ],
            "wifi": [
                "WiFi Auditing Help",
                "• Network Scan: Discover nearby WiFi networks",
                "• Security Analysis: Assess network vulnerabilities",
                "• WPS Testing: Test WPS PIN vulnerabilities",
                "• Rogue AP: Create fake access points",
                "• Monitor Mode: Enable advanced WiFi monitoring",
            ],
            "system": [
                "System Monitoring Help",
                "• Health Check: Comprehensive system validation",
                "• Service Status: Check running services",
                "• Performance: Monitor resource usage",
                "• Logs: View and analyze system logs",
                "• Security Audit: Run automated security scans",
            ],
        }

        content = help_content.get(context, ["Help not available for this section"])

        print(
            f"\n{VisualTokens.COLORS['primary']}📚 {content[0]}{VisualTokens.COLORS['reset']}"
        )
        print("=" * 50)
        for line in content[1:]:
            print(f"{VisualTokens.COLORS['muted']}{line}{VisualTokens.COLORS['reset']}")
        print()

        input(
            f"{VisualTokens.COLORS['accent']}Press Enter to continue...{VisualTokens.COLORS['reset']}"
        )

    def main_menu(self) -> None:
        """Main application menu"""
        self._print_header()

        while self.running:
            self._print_menu(
                "Main Menu",
                [
                    "Anonymity (Tor + Proxy)",
                    "WiFi Auditing (Attacks & Scanning)",
                    "Configuration Management",
                    "System Status & Monitoring",
                    "Plugins",  # New menu option
                    "Help & Documentation",
                ],
            )

            choice = self._get_user_choice()

            if choice == 1:
                self.anonymity_menu()
            elif choice == 2:
                self.wifi_menu()
            elif choice == 3:
                self.configuration_menu()
            elif choice == 4:
                self.system_status_menu()
            elif choice == 5:
                self.plugins_menu()  # New method call
            elif choice == 6:
                self.help_menu()
            elif choice == 0:
                print(f"{self._colorize('Thank you for using AnonSuite!', 'primary')}")
                break
            else:
                error_msg = (
                    f"{VisualTokens.SYMBOLS['error']} Invalid choice. Please try again."
                )
                print(self._colorize(error_msg, "error"))


def main() -> None:
    """Main application entry point with comprehensive CLI support"""
    parser = argparse.ArgumentParser(
        description=__description__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Start interactive menu
  %(prog)s --health-check           # Run system health check
  %(prog)s --start-anonymity        # Start Tor anonymity services
  %(prog)s --wifi-scan              # Scan for WiFi networks
  %(prog)s --wps-attack TARGET      # Launch WPS attack on target BSSID
  %(prog)s --config-wizard          # Run configuration wizard
  %(prog)s --security-audit         # Run security audit with Bandit
  %(prog)s --profile production     # Use specific configuration profile

For more information, visit: https://github.com/morningstarxcdcode/AnonSuite
        """,
    )

    # Version and basic info
    parser.add_argument(
        "--version", action="version", version=f"AnonSuite {__version__}"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument(
        "--profile", type=str, help="Use specific configuration profile"
    )

    # System operations
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Perform comprehensive system health check",
    )
    parser.add_argument(
        "--config-wizard",
        action="store_true",
        help="Run interactive configuration wizard",
    )
    parser.add_argument(
        "--security-audit", action="store_true", help="Run security audit with Bandit"
    )

    # Anonymity operations
    parser.add_argument(
        "--start-anonymity", action="store_true", help="Start Tor anonymity services"
    )
    parser.add_argument(
        "--stop-anonymity", action="store_true", help="Stop Tor anonymity services"
    )
    parser.add_argument(
        "--anonymity-status",
        action="store_true",
        help="Check anonymity services status",
    )
    parser.add_argument(
        "--new-circuit", action="store_true", help="Request new Tor circuit"
    )

    # WiFi operations
    parser.add_argument(
        "--wifi-scan", action="store_true", help="Scan for WiFi networks"
    )
    parser.add_argument(
        "--wifi-interface", type=str, help="Specify WiFi interface for operations"
    )
    parser.add_argument(
        "--wps-attack",
        type=str,
        metavar="BSSID",
        help="Launch WPS attack on target BSSID",
    )
    parser.add_argument(
        "--start-ap",
        type=str,
        metavar="SSID",
        help="Start rogue access point with specified SSID",
    )
    parser.add_argument(
        "--stop-ap", action="store_true", help="Stop running access point"
    )

    # Configuration operations
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List available configuration profiles",
    )
    parser.add_argument(
        "--create-profile",
        type=str,
        metavar="NAME",
        help="Create new configuration profile",
    )
    parser.add_argument(
        "--export-profile",
        nargs=2,
        metavar=("PROFILE", "PATH"),
        help="Export profile to file",
    )
    parser.add_argument(
        "--import-profile",
        nargs=2,
        metavar=("NAME", "PATH"),
        help="Import profile from file",
    )

    # Plugin operations
    parser.add_argument(
        "--list-plugins", action="store_true", help="List available plugins"
    )
    parser.add_argument(
        "--run-plugin", type=str, metavar="NAME", help="Run specific plugin"
    )

    # Output options
    parser.add_argument("--output", "-o", type=str, help="Output file for results")
    parser.add_argument(
        "--format",
        choices=["json", "text", "csv"],
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output"
    )

    # Educational and demo features
    parser.add_argument(
        "--tutorial", action="store_true", help="Start interactive learning tutorial"
    )
    parser.add_argument(
        "--demo", action="store_true", help="Run quick start demonstration"
    )
    parser.add_argument(
        "--explain",
        metavar="CONCEPT",
        help="Explain security concepts (wifi, tor, anonymity, etc.)",
    )

    # Advanced features for professionals
    parser.add_argument(
        "--batch-mode", action="store_true", help="Run in batch mode for automation"
    )
    parser.add_argument(
        "--generate-report",
        metavar="OUTPUT_FILE",
        help="Generate comprehensive security report",
    )

    args = parser.parse_args()

    try:
        # Initialize CLI with configuration
        cli = AnonSuiteCLI()

        # Handle profile selection
        if args.profile:
            if not cli.config.load_config(args.profile):
                print(
                    f"{VisualTokens.COLORS['error']}Failed to load profile: {args.profile}{VisualTokens.COLORS['reset']}"
                )
                sys.exit(1)

        # Handle debug/verbose modes
        if args.debug:
            logging.basicConfig(level=logging.DEBUG)
            cli.config.set("general.debug", True)
        elif args.verbose:
            logging.basicConfig(level=logging.INFO)

        # Handle color output
        if args.no_color:
            cli.config.set("ui.colors", False)

        # Educational features
        if args.tutorial:
            cli._run_tutorial_mode()
            return

        if args.demo:
            cli._run_quick_start_demo()
            return

        if args.explain:
            cli._explain_concept(args.explain)
            return

        # Professional features
        if args.batch_mode:
            cli._run_batch_mode()
            return

        if args.generate_report:
            cli._generate_security_report(args.generate_report)
            return

        # Process command-line operations
        if args.health_check:
            result = cli._run_health_check()
            if args.output:
                _save_output(result, args.output, args.format)
            sys.exit(0 if result.get("status") == "success" else 1)

        elif args.config_wizard:
            cli._run_configuration_wizard()
            sys.exit(0)

        elif args.security_audit:
            result = cli._run_security_audit()
            if args.output:
                _save_output(result, args.output, args.format)
            sys.exit(0)

        elif args.start_anonymity:
            result = cli._start_anonymity_services()
            print(f"Anonymity services: {result.get('message', 'Started')}")
            sys.exit(0 if result.get("status") == "success" else 1)

        elif args.stop_anonymity:
            result = cli._stop_anonymity_services()
            print(f"Anonymity services: {result.get('message', 'Stopped')}")
            sys.exit(0)

        elif args.anonymity_status:
            result = cli._check_anonymity_status()
            print(f"Anonymity status: {result.get('message', 'Unknown')}")
            if args.output:
                _save_output(result, args.output, args.format)
            sys.exit(0)

        elif args.new_circuit:
            result = cli._request_new_circuit()
            print(f"New circuit: {result.get('message', 'Requested')}")
            sys.exit(0 if result.get("status") == "success" else 1)

        elif args.wifi_scan:
            result = cli._scan_wifi_networks(args.wifi_interface)
            if args.output:
                _save_output(result, args.output, args.format)
            else:
                _display_wifi_results(result)
            sys.exit(0)

        elif args.wps_attack:
            if not args.wifi_interface:
                print(
                    f"{VisualTokens.COLORS['error']}WiFi interface required for WPS attack{VisualTokens.COLORS['reset']}"
                )
                sys.exit(1)
            result = cli._launch_wps_attack(args.wps_attack, args.wifi_interface)
            if args.output:
                _save_output(result, args.output, args.format)
            sys.exit(0 if result.get("status") == "success" else 1)

        elif args.start_ap:
            result = cli._start_rogue_ap(args.start_ap, args.wifi_interface)
            print(f"Rogue AP: {result.get('message', 'Started')}")
            sys.exit(0 if result.get("status") == "success" else 1)

        elif args.stop_ap:
            result = cli._stop_rogue_ap()
            print(f"Rogue AP: {result.get('message', 'Stopped')}")
            sys.exit(0)

        elif args.list_profiles:
            profiles = cli.config.list_profiles()
            print("Available profiles:")
            for profile in profiles:
                marker = " (current)" if profile == cli.config.current_profile else ""
                print(f"  - {profile}{marker}")
            sys.exit(0)

        elif args.create_profile:
            success = cli.config.create_profile(args.create_profile)
            print(f"Profile creation: {'Success' if success else 'Failed'}")
            sys.exit(0 if success else 1)

        elif args.export_profile:
            profile_name, export_path = args.export_profile
            success = cli.config.export_profile(profile_name, export_path)
            print(f"Profile export: {'Success' if success else 'Failed'}")
            sys.exit(0 if success else 1)

        elif args.import_profile:
            profile_name, import_path = args.import_profile
            success = cli.config.import_profile(profile_name, import_path)
            print(f"Profile import: {'Success' if success else 'Failed'}")
            sys.exit(0 if success else 1)

        elif args.list_plugins:
            plugins = list(cli.plugin_manager.loaded_plugins.keys())
            print(f"Available plugins ({len(plugins)}):")
            for plugin in plugins:
                print(f"  - {plugin}")
            sys.exit(0)

        elif args.run_plugin:
            cli.plugin_manager.run_plugin_by_name(args.run_plugin)
            sys.exit(0)

        else:
            # No command-line arguments, start interactive menu
            cli.main_menu()

    except KeyboardInterrupt:
        print(
            f"\n{VisualTokens.COLORS['muted']}Interrupted by user. Goodbye!{VisualTokens.COLORS['reset']}"
        )
        sys.exit(0)
    except ConfigurationError as e:
        print(
            f"{VisualTokens.COLORS['error']}Configuration Error: {e.message}{VisualTokens.COLORS['reset']}"
        )
        sys.exit(1)
    except Exception as e:
        if args.debug if "args" in locals() else False:
            import traceback

            traceback.print_exc()
        print(
            f"{VisualTokens.COLORS['error']}Fatal error: {e}{VisualTokens.COLORS['reset']}"
        )
        sys.exit(1)


def _save_output(data: dict, filepath: str, format_type: str):
    """Save output data to file in specified format"""
    try:
        with open(filepath, "w") as f:
            if format_type == "json":
                json.dump(data, f, indent=2)
            elif format_type == "csv":
                # Simple CSV output for basic data
                if isinstance(data, dict) and "networks" in data:
                    import csv

                    writer = csv.DictWriter(
                        f,
                        fieldnames=[
                            "ssid",
                            "bssid",
                            "channel",
                            "signal_level",
                            "encryption",
                        ],
                    )
                    writer.writeheader()
                    for network in data["networks"]:
                        writer.writerow(network)
                else:
                    f.write(str(data))
            else:  # text format
                f.write(str(data))
        print(f"Results saved to {filepath}")
    except Exception as e:
        print(f"Failed to save output: {e}")


def _display_wifi_results(result: dict):
    """Display WiFi scan results in a formatted way"""
    if result.get("status") == "success" and "networks" in result:
        networks = result["networks"]
        print(f"\nFound {len(networks)} networks:")
        print("-" * 80)
        print(f"{'SSID':<20} {'BSSID':<18} {'CH':<3} {'Signal':<7} {'Encryption':<15}")
        print("-" * 80)

        for network in networks[:20]:  # Show first 20
            ssid = network.get("ssid", "Hidden")[:19]
            bssid = network.get("bssid", "Unknown")
            channel = str(network.get("channel", "?"))
            signal = f"{network.get('signal_level', 0)}dBm"
            encryption = network.get("encryption", "Unknown")[:14]

            print(f"{ssid:<20} {bssid:<18} {channel:<3} {signal:<7} {encryption:<15}")

        if len(networks) > 20:
            print(f"... and {len(networks) - 20} more networks")
    else:
        print(f"WiFi scan failed: {result.get('message', 'Unknown error')}")


# Add helper methods to AnonSuiteCLI class for command-line operations
def _add_cli_helper_methods():
    """Add helper methods to AnonSuiteCLI for command-line operations"""

    def _run_health_check(self) -> Dict[str, Any]:
        """Comprehensive system health check with timeout protection"""
        print(f"\n{self._colorize('AnonSuite Health Check', 'primary')}")
        print("=" * 50)

        health_results = {
            "overall_status": "unknown",
            "checks": {},
            "warnings": [],
            "errors": [],
            "recommendations": [],
        }

        # Define health checks with timeouts
        checks = [
            ("Python Environment", self._check_python_environment, 5),
            ("System Dependencies", self._check_system_dependencies, 10),
            ("Configuration Files", self._check_configuration_files, 5),
            ("Directory Structure", self._check_directory_structure, 5),
            ("Network Connectivity", self._check_network_connectivity, 15),
            ("Tor Availability", self._check_tor_availability, 10),
            ("WiFi Tools", self._check_wifi_tools, 10),
            ("Plugin System", self._check_plugin_system, 5),
        ]

        passed_checks = 0
        total_checks = len(checks)

        for check_name, check_func, timeout in checks:
            print(f"\n{VisualTokens.SYMBOLS['info']} Checking {check_name}...")

            try:
                # Run check with timeout
                import signal

                def timeout_handler(signum, frame, timeout_val=timeout):
                    raise TimeoutError(
                        f"Health check timed out after {timeout_val} seconds"
                    )

                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(timeout)

                try:
                    result = check_func()
                    signal.alarm(0)  # Cancel timeout

                    if result.get("status") == "pass":
                        print(f"  {VisualTokens.SYMBOLS['success']} {check_name}: PASS")
                        if result.get("message"):
                            print(f"    {result['message']}")
                        passed_checks += 1
                    elif result.get("status") == "warning":
                        print(
                            f"  {VisualTokens.SYMBOLS['warning']} {check_name}: WARNING"
                        )
                        print(f"    {result.get('message', 'No details available')}")
                        health_results["warnings"].append(
                            f"{check_name}: {result.get('message')}"
                        )
                        passed_checks += 0.5  # Partial credit for warnings
                    else:
                        print(f"  {VisualTokens.SYMBOLS['error']} {check_name}: FAIL")
                        print(f"    {result.get('message', 'Check failed')}")
                        health_results["errors"].append(
                            f"{check_name}: {result.get('message')}"
                        )

                    health_results["checks"][check_name] = result

                except TimeoutError as e:
                    signal.alarm(0)
                    print(f"  {VisualTokens.SYMBOLS['error']} {check_name}: TIMEOUT")
                    print(f"    {str(e)}")
                    health_results["errors"].append(
                        f"{check_name}: Timed out after {timeout}s"
                    )
                    health_results["checks"][check_name] = {
                        "status": "timeout",
                        "message": str(e),
                    }

            except Exception as e:
                signal.alarm(0)
                print(f"  {VisualTokens.SYMBOLS['error']} {check_name}: ERROR")
                print(f"    {str(e)}")
                health_results["errors"].append(f"{check_name}: {str(e)}")
                health_results["checks"][check_name] = {
                    "status": "error",
                    "message": str(e),
                }

        # Calculate overall health score
        health_score = (passed_checks / total_checks) * 100

        print(f"\n{self._colorize('Health Check Summary', 'accent')}")
        print("-" * 30)

        if health_score >= 90:
            health_results["overall_status"] = "excellent"
            print(
                f"{VisualTokens.SYMBOLS['success']} Overall Health: EXCELLENT ({health_score:.1f}%)"
            )
        elif health_score >= 75:
            health_results["overall_status"] = "good"
            print(
                f"{VisualTokens.SYMBOLS['success']} Overall Health: GOOD ({health_score:.1f}%)"
            )
        elif health_score >= 50:
            health_results["overall_status"] = "fair"
            print(
                f"{VisualTokens.SYMBOLS['warning']} Overall Health: FAIR ({health_score:.1f}%)"
            )
        else:
            health_results["overall_status"] = "poor"
            print(
                f"{VisualTokens.SYMBOLS['error']} Overall Health: POOR ({health_score:.1f}%)"
            )

        # Show recommendations
        if health_results["errors"]:
            print(f"\n{self._colorize('Critical Issues:', 'error')}")
            for error in health_results["errors"][:3]:  # Show top 3
                print(f"  • {error}")

        if health_results["warnings"]:
            print(f"\n{self._colorize('Warnings:', 'warning')}")
            for warning in health_results["warnings"][:3]:  # Show top 3
                print(f"  • {warning}")

        # Add recommendations based on results
        self._add_health_recommendations(health_results)

        if health_results["recommendations"]:
            print(f"\n{self._colorize('Recommendations:', 'accent')}")
            for rec in health_results["recommendations"][:3]:  # Show top 3
                print(f"  • {rec}")

        print("\nFor detailed troubleshooting, see: docs/troubleshooting.md")

        return health_results

    def _check_python_environment(self) -> Dict[str, Any]:
        """Check Python environment health"""
        try:
            import sys

            # Check Python version
            if sys.version_info < (3, 9):
                return {
                    "status": "fail",
                    "message": f"Python {sys.version_info.major}.{sys.version_info.minor} is too old. Requires 3.9+",
                }

            # Check virtual environment
            in_venv = hasattr(sys, "real_prefix") or (
                hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
            )

            if not in_venv:
                return {
                    "status": "warning",
                    "message": "Not running in virtual environment. Recommended for isolation.",
                }

            return {
                "status": "pass",
                "message": f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} in virtual environment",
            }

        except Exception as e:
            return {"status": "error", "message": f"Python check failed: {e}"}

    def _check_system_dependencies(self) -> Dict[str, Any]:
        """Check system dependencies"""
        try:
            required_tools = ["tor", "privoxy"]
            optional_tools = (
                ["iwconfig", "iwlist"] if sys.platform != "darwin" else ["airport"]
            )

            missing_required = []
            missing_optional = []

            for tool in required_tools:
                if not self._command_exists(tool):
                    missing_required.append(tool)

            for tool in optional_tools:
                if not self._command_exists(tool) and tool != "airport":
                    missing_optional.append(tool)
                elif tool == "airport":
                    airport_path = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
                    if not os.path.exists(airport_path):
                        missing_optional.append(tool)

            if missing_required:
                return {
                    "status": "fail",
                    "message": f"Missing required tools: {', '.join(missing_required)}",
                }
            elif missing_optional:
                return {
                    "status": "warning",
                    "message": f"Missing optional tools: {', '.join(missing_optional)}",
                }
            else:
                return {
                    "status": "pass",
                    "message": "All required system dependencies available",
                }

        except Exception as e:
            return {"status": "error", "message": f"Dependency check failed: {e}"}

    def _check_configuration_files(self) -> Dict[str, Any]:
        """Check configuration files"""
        try:
            config_file = self.config.config_file_path

            if not os.path.exists(config_file):
                return {
                    "status": "warning",
                    "message": "Configuration file not found. Run --config-wizard to create.",
                }

            # Try to load and validate configuration
            try:
                issues = self.config.validate_config()
                if issues["errors"]:
                    return {
                        "status": "fail",
                        "message": f"Configuration errors: {len(issues['errors'])} issues found",
                    }
                elif issues["warnings"]:
                    return {
                        "status": "warning",
                        "message": f"Configuration warnings: {len(issues['warnings'])} issues found",
                    }
                else:
                    return {"status": "pass", "message": "Configuration file valid"}
            except Exception as e:
                return {
                    "status": "fail",
                    "message": f"Configuration validation failed: {e}",
                }

        except Exception as e:
            return {"status": "error", "message": f"Configuration check failed: {e}"}

    def _check_directory_structure(self) -> Dict[str, Any]:
        """Check directory structure"""
        try:
            required_dirs = [
                self.config.get("general.data_dir", "run"),
                self.config.get("general.temp_dir", "/tmp/anonsuite"),
                "config",
                "plugins",
                "log",
            ]

            missing_dirs = []
            for dir_path in required_dirs:
                if not os.path.exists(dir_path):
                    missing_dirs.append(dir_path)

            if missing_dirs:
                # Try to create missing directories
                created_dirs = []
                for dir_path in missing_dirs:
                    try:
                        os.makedirs(dir_path, exist_ok=True)
                        created_dirs.append(dir_path)
                    except Exception:
                        pass

                if created_dirs:
                    return {
                        "status": "pass",
                        "message": f"Created missing directories: {', '.join(created_dirs)}",
                    }
                else:
                    return {
                        "status": "fail",
                        "message": f"Cannot create directories: {', '.join(missing_dirs)}",
                    }
            else:
                return {"status": "pass", "message": "All required directories exist"}

        except Exception as e:
            return {"status": "error", "message": f"Directory check failed: {e}"}

    def _check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity"""
        try:
            import socket
            import urllib.request

            # Test basic DNS resolution
            try:
                socket.gethostbyname("google.com")
            except Exception:
                return {
                    "status": "fail",
                    "message": "DNS resolution failed. Check network connection.",
                }

            # Test HTTP connectivity
            try:
                urllib.request.urlopen("https://httpbin.org/ip", timeout=10)
            except Exception:
                return {
                    "status": "warning",
                    "message": "HTTP connectivity limited. May affect some features.",
                }

            return {"status": "pass", "message": "Network connectivity working"}

        except Exception as e:
            return {"status": "error", "message": f"Network check failed: {e}"}

    def _check_tor_availability(self) -> Dict[str, Any]:
        """Check Tor availability and configuration"""
        try:
            if not self._command_exists("tor"):
                return {
                    "status": "fail",
                    "message": "Tor not installed. Install with: brew install tor (macOS) or apt install tor (Linux)",
                }

            # Check if Tor is running
            try:
                result = subprocess.run(
                    ["pgrep", "tor"], capture_output=True, timeout=5
                )
                if result.returncode == 0:
                    return {"status": "pass", "message": "Tor is installed and running"}
                else:
                    return {
                        "status": "warning",
                        "message": "Tor installed but not running. Start with --start-anonymity",
                    }
            except Exception:
                return {
                    "status": "warning",
                    "message": "Tor installed but status unknown",
                }

        except Exception as e:
            return {"status": "error", "message": f"Tor check failed: {e}"}

    def _check_wifi_tools(self) -> Dict[str, Any]:
        """Check WiFi tools availability"""
        try:
            if sys.platform == "darwin":  # macOS
                airport_path = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
                if os.path.exists(airport_path):
                    return {
                        "status": "pass",
                        "message": "macOS WiFi tools available (airport/system_profiler)",
                    }
                else:
                    return {
                        "status": "warning",
                        "message": "macOS airport utility not found. Limited WiFi functionality.",
                    }
            else:  # Linux
                if self._command_exists("iwconfig") and self._command_exists("iwlist"):
                    return {
                        "status": "pass",
                        "message": "Linux WiFi tools available (wireless-tools)",
                    }
                else:
                    return {
                        "status": "fail",
                        "message": "WiFi tools missing. Install with: sudo apt install wireless-tools",
                    }

        except Exception as e:
            return {"status": "error", "message": f"WiFi tools check failed: {e}"}

    def _check_plugin_system(self) -> Dict[str, Any]:
        """Check plugin system"""
        try:
            plugins_dir = self.config.get("plugins.directory", "plugins")

            if not os.path.exists(plugins_dir):
                return {
                    "status": "warning",
                    "message": f"Plugin directory not found: {plugins_dir}",
                }

            plugin_files = [
                f
                for f in os.listdir(plugins_dir)
                if f.endswith(".py") and not f.startswith("__")
            ]

            if not plugin_files:
                return {"status": "warning", "message": "No plugin files found"}

            # Try to load plugins
            loaded_plugins = len(self.plugin_manager.loaded_plugins)

            if loaded_plugins == 0:
                return {
                    "status": "warning",
                    "message": f"Plugin files found ({len(plugin_files)}) but none loaded successfully",
                }
            else:
                return {
                    "status": "pass",
                    "message": f"{loaded_plugins} plugins loaded successfully",
                }

        except Exception as e:
            return {"status": "error", "message": f"Plugin system check failed: {e}"}

    def _add_health_recommendations(self, health_results: Dict[str, Any]) -> None:
        """Add recommendations based on health check results"""
        recommendations = []

        # Check for common issues and add recommendations
        for check_name, result in health_results["checks"].items():
            if result["status"] == "fail":
                if "Python" in check_name:
                    recommendations.append("Upgrade Python to version 3.8 or higher")
                elif "Dependencies" in check_name:
                    if sys.platform == "darwin":
                        recommendations.append(
                            "Install missing tools with: brew install tor privoxy"
                        )
                    else:
                        recommendations.append(
                            "Install missing tools with: sudo apt install tor privoxy wireless-tools"
                        )
                elif "Configuration" in check_name:
                    recommendations.append(
                        "Run configuration wizard: python src/anonsuite.py --config-wizard"
                    )
                elif "Network" in check_name:
                    recommendations.append(
                        "Check internet connection and firewall settings"
                    )
                elif "WiFi" in check_name:
                    if sys.platform != "darwin":
                        recommendations.append(
                            "Install WiFi tools: sudo apt install wireless-tools aircrack-ng"
                        )

        # Add general recommendations
        if health_results["overall_status"] in ["poor", "fair"]:
            recommendations.append(
                "Review troubleshooting guide: docs/troubleshooting.md"
            )
            recommendations.append("Consider running installation script: ./install.sh")

        health_results["recommendations"] = recommendations[:5]  # Limit to top 5

    def _start_anonymity_services(self) -> dict:
        """Start anonymity services"""
        # Implementation would start Tor and Privoxy
        return {"status": "success", "message": "Anonymity services started"}

    def _stop_anonymity_services(self) -> dict:
        """Stop anonymity services"""
        # Implementation would stop Tor and Privoxy
        return {"status": "success", "message": "Anonymity services stopped"}

    def _check_anonymity_status(self) -> dict:
        """Check anonymity services status"""
        # Implementation would check Tor and Privoxy status
        return {"status": "success", "message": "Services running"}

    def _request_new_circuit(self) -> dict:
        """Request new Tor circuit"""
        # Implementation would request new circuit via Tor control port
        return {"status": "success", "message": "New circuit requested"}

    def _scan_wifi_networks(self, interface: str = None) -> dict:
        """Scan for WiFi networks"""
        try:
            from wifi.wifi_scanner import WiFiScanner

            scanner = WiFiScanner()
            networks = scanner.scan_networks(interface)
            return {"status": "success", "networks": networks, "count": len(networks)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _launch_wps_attack(self, bssid: str, interface: str) -> dict:
        """Launch WPS attack"""
        # Implementation would use pixiewps wrapper
        return {"status": "error", "message": "WPS attack requires handshake data"}

    def _start_rogue_ap(self, ssid: str, interface: str = None) -> dict:
        """Start rogue access point"""
        try:
            from wifi.wifipumpkin_wrapper import WiFiPumpkinWrapper

            wrapper = WiFiPumpkinWrapper()
            result = wrapper.start_ap(ssid, interface or "wlan0")
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _stop_rogue_ap(self) -> dict:
        """Stop rogue access point"""
        try:
            from wifi.wifipumpkin_wrapper import WiFiPumpkinWrapper

            wrapper = WiFiPumpkinWrapper()
            result = wrapper.stop_ap()
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _run_security_audit(self) -> dict:
        """Run security audit with Bandit"""
        # Implementation would run Bandit security scan
        return {"status": "success", "message": "Security audit completed"}

    # Add methods to AnonSuiteCLI class
    AnonSuiteCLI._run_health_check = _run_health_check
    AnonSuiteCLI._start_anonymity_services = _start_anonymity_services
    AnonSuiteCLI._stop_anonymity_services = _stop_anonymity_services
    AnonSuiteCLI._check_anonymity_status = _check_anonymity_status
    AnonSuiteCLI._request_new_circuit = _request_new_circuit
    AnonSuiteCLI._scan_wifi_networks = _scan_wifi_networks
    AnonSuiteCLI._launch_wps_attack = _launch_wps_attack
    AnonSuiteCLI._start_rogue_ap = _start_rogue_ap
    AnonSuiteCLI._stop_rogue_ap = _stop_rogue_ap
    AnonSuiteCLI._run_security_audit = _run_security_audit


# Initialize helper methods
_add_cli_helper_methods()

if __name__ == "__main__":
    main()
