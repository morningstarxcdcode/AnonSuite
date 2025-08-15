#!/usr/bin/env python3
"""
Sample AnonSuite Plugin
Demonstrates the plugin system functionality
"""

import subprocess
import platform
import sys
import os

# Add the src directory to path to import the base class
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

try:
    from anonsuite import AnonSuitePlugin
except ImportError:
    # Fallback base class if import fails
    class AnonSuitePlugin:
        def __init__(self, cli_instance):
            self.cli = cli_instance
        def run(self, *args, **kwargs):
            raise NotImplementedError("Plugins must implement the run() method.")
        def get_menu_option(self) -> str:
            return f"{getattr(self, 'name', 'Unknown')} ({getattr(self, 'description', 'No description')})"

class NetworkInfoPlugin(AnonSuitePlugin):
    """Sample plugin for displaying network information"""
    
    def __init__(self, cli_instance):
        super().__init__(cli_instance)
        self.name = "Network Info Plugin"
        self.version = "1.0.0"
        self.description = "Display basic network information"
    
    def run(self, *args, **kwargs):
        """Execute the plugin functionality"""
        print(f"\n🔌 Executing {self.name} v{self.version}...")
        print("=" * 60)
        
        # Get system info
        print(f"🖥️  System: {platform.system()} {platform.release()}")
        print(f"🏗️  Architecture: {platform.machine()}")
        print(f"🐍 Python: {platform.python_version()}")
        
        # Get network interfaces (basic)
        try:
            if platform.system() == "Darwin":  # macOS
                result = subprocess.run(["ifconfig"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    interfaces = []
                    for line in lines:
                        if line and not line.startswith(' ') and not line.startswith('\t') and ':' in line:
                            interface = line.split(':')[0]
                            if interface and not interface.startswith('lo'):  # Skip loopback
                                interfaces.append(interface)
                    print(f"🌐 Active Interfaces: {', '.join(interfaces[:5])}")  # Show first 5
                else:
                    print("🌐 Network Interfaces: Unable to retrieve")
            else:
                print("🌐 Network Interfaces: Not implemented for this OS")
        except Exception as e:
            print(f"🌐 Network Interfaces: Error - {str(e)}")
        
        # Check internet connectivity
        try:
            result = subprocess.run(["ping", "-c", "1", "8.8.8.8"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("🌍 Internet: Connected")
            else:
                print("🌍 Internet: Not connected")
        except Exception:
            print("🌍 Internet: Unable to test")
        
        print("=" * 60)
        print("✅ Plugin execution completed!")
        print("\nPress Enter to continue...")
        input()
        
        return {"status": "success", "message": "Network info plugin executed"}
