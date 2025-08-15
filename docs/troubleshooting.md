# AnonSuite Troubleshooting Guide

This guide covers common issues and their solutions based on real-world usage and user feedback.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Configuration Problems](#configuration-problems)
- [Anonymity Service Issues](#anonymity-service-issues)
- [WiFi Tool Problems](#wifi-tool-problems)
- [Plugin System Issues](#plugin-system-issues)
- [Performance Problems](#performance-problems)
- [Error Messages](#error-messages)
- [Getting Help](#getting-help)

## Installation Issues

### Python Version Compatibility

**Problem**: "AnonSuite requires Python 3.8 or higher"

**Solution**:
```bash
# Check your Python version
python3 --version

# Install Python 3.8+ if needed (macOS)
brew install python@3.11

# Install Python 3.8+ if needed (Ubuntu/Debian)
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-pip
```

### Virtual Environment Issues

**Problem**: "No module named 'venv'" or virtual environment creation fails

**Solution**:
```bash
# Install venv module (Ubuntu/Debian)
sudo apt install python3-venv

# Alternative: use virtualenv
pip3 install virtualenv
virtualenv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
```

### Permission Denied Errors

**Problem**: Permission denied when running scripts or accessing files

**Solution**:
```bash
# Fix script permissions
chmod +x src/anonymity/multitor/multitor
chmod +x install.sh

# Fix directory ownership
sudo chown -R $USER:$USER /Users/morningstar/Desktop/AnonSuite

# Create directories with proper permissions
mkdir -p run log config/profiles plugins
chmod 755 run log config
```

### Missing System Dependencies

**Problem**: "Command not found" for system tools

**Solution**:
```bash
# macOS - Install missing tools
brew install tor privoxy git

# Ubuntu/Debian - Install missing tools
sudo apt update
sudo apt install tor privoxy python3-pip git wireless-tools net-tools

# Fedora/CentOS - Install missing tools
sudo dnf install tor privoxy python3-pip git wireless-tools net-tools
```

## Configuration Problems

### Configuration File Not Found

**Problem**: "Configuration file not found" or JSON decode errors

**Solution**:
```bash
# Create missing directories
mkdir -p config/profiles run log

# Run configuration wizard
python src/anonsuite.py --config-wizard

# Or create default config manually
cp config/anonsuite.conf.example config/anonsuite.conf
```

### Invalid JSON Configuration

**Problem**: "Expecting value: line 1 column 1 (char 0)" or JSON decode errors

**Solution**:
```bash
# Validate JSON syntax
python -m json.tool config/anonsuite.conf

# Reset to default configuration
rm config/anonsuite.conf
python src/anonsuite.py --config-wizard

# Check for hidden characters
cat -A config/anonsuite.conf | head -5
```

### Profile Loading Issues

**Problem**: "Profile 'name' not found" or profile switching fails

**Solution**:
```bash
# List available profiles
python src/anonsuite.py --list-profiles

# Create missing profile
python src/anonsuite.py --create-profile production

# Check profile directory
ls -la config/profiles/

# Verify profile file format
python -m json.tool config/profiles/production.json
```

## Anonymity Service Issues

### Tor Connection Problems

**Problem**: Tor fails to start or connect

**Solution**:
```bash
# Check if Tor is already running
ps aux | grep tor
lsof -i :9050  # Default Tor port
lsof -i :9000  # AnonSuite Tor port

# Kill existing Tor processes
sudo pkill tor

# Check Tor configuration
sudo nano /opt/homebrew/etc/tor/torrc  # macOS
sudo nano /etc/tor/torrc               # Linux

# Start Tor manually for debugging
tor -f /opt/homebrew/etc/tor/torrc --verify-config
```

### Port Conflicts

**Problem**: "Address already in use" or port binding errors

**Solution**:
```bash
# Check what's using the ports
lsof -i :9000  # Tor SOCKS port
lsof -i :9001  # Tor control port
lsof -i :8119  # Privoxy port

# Kill conflicting processes
sudo kill <PID>

# Change ports in configuration
nano config/anonsuite.conf
# Update tor.socks_port and tor.control_port
```

### Privoxy Configuration Issues

**Problem**: Privoxy not forwarding to Tor or configuration errors

**Solution**:
```bash
# Check Privoxy configuration
sudo nano /opt/homebrew/etc/privoxy/config  # macOS
sudo nano /etc/privoxy/config               # Linux

# Ensure these lines are present:
# listen-address 127.0.0.1:8119
# forward-socks5 / 127.0.0.1:9000 .

# Restart Privoxy
sudo brew services restart privoxy  # macOS
sudo systemctl restart privoxy     # Linux

# Test Privoxy connection
curl --proxy 127.0.0.1:8119 https://httpbin.org/ip
```

### Directory Ownership Problems

**Problem**: "Permission denied" when accessing Tor data directory

**Solution**:
```bash
# Fix Tor data directory ownership
sudo chown -R $USER src/anonymity/multitor/tor_9000

# Create directory if missing
mkdir -p src/anonymity/multitor/tor_9000
chmod 700 src/anonymity/multitor/tor_9000

# Check directory permissions
ls -la src/anonymity/multitor/
```

## WiFi Tool Problems

### WiFi Interface Not Found

**Problem**: "No wireless interfaces found" or interface errors

**Solution**:
```bash
# List available interfaces
iwconfig  # Linux
system_profiler SPAirPortDataType  # macOS

# Check interface status
ip link show  # Linux
ifconfig      # macOS/Linux

# Bring interface up
sudo ip link set wlan0 up  # Linux
sudo ifconfig wlan0 up     # macOS (if supported)
```

### Pixiewps Binary Issues

**Problem**: "Pixiewps binary not found" or compilation errors

**Solution**:
```bash
# Check if binary exists
ls -la src/wifi/pixiewps/pixiewps

# Compile pixiewps if missing
cd src/wifi/pixiewps
make clean
make

# Install build dependencies if compilation fails
sudo apt install build-essential  # Ubuntu/Debian
brew install gcc                   # macOS
```

### WiFiPumpkin3 Dependencies

**Problem**: "WiFiPumpkin3 functionality not available" or import errors

**Solution**:
```bash
# Install PyQt5 dependencies
pip install PyQt5 PyQt5-tools

# Install network dependencies
pip install scapy netfilterqueue

# Check Python path
python -c "import sys; print(sys.path)"

# Test imports manually
python -c "import PyQt5; print('PyQt5 OK')"
python -c "import scapy; print('Scapy OK')"
```

### Monitor Mode Issues

**Problem**: Cannot enable monitor mode or interface errors

**Solution**:
```bash
# Check if interface supports monitor mode
iw list | grep -A 10 "Supported interface modes"

# Enable monitor mode (Linux)
sudo airmon-ng start wlan0

# Alternative method
sudo ip link set wlan0 down
sudo iw wlan0 set monitor control
sudo ip link set wlan0 up

# Note: Monitor mode not available on macOS built-in WiFi
```

## Plugin System Issues

### Plugins Not Loading

**Problem**: "No plugins found" or plugin loading errors

**Solution**:
```bash
# Check plugins directory
ls -la plugins/

# Verify plugin file format
python -c "
import sys
sys.path.append('plugins')
import sample_plugin
print('Plugin loaded successfully')
"

# Check plugin inheritance
grep -n "class.*Plugin" plugins/*.py

# Test plugin manually
python plugins/sample_plugin.py
```

### Plugin Import Errors

**Problem**: "ModuleNotFoundError" or import issues in plugins

**Solution**:
```bash
# Check Python path in plugin
head -10 plugins/sample_plugin.py

# Verify src directory is accessible
python -c "
import sys
sys.path.append('src')
from config_manager import ConfigManager
print('Import successful')
"

# Fix plugin imports
# Add this to plugin file:
# import sys, os
# sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
```

### Plugin Execution Errors

**Problem**: Plugins load but fail to execute

**Solution**:
```bash
# Check plugin class structure
grep -A 10 "class.*Plugin" plugins/sample_plugin.py

# Verify required methods exist
grep -n "def run\|def __init__" plugins/sample_plugin.py

# Test plugin execution
python src/anonsuite.py --run-plugin "Network Info Plugin"

# Check for missing dependencies in plugin
python -c "
import subprocess, platform, sys, os
print('Plugin dependencies available')
"
```

## Performance Problems

### Slow Startup

**Problem**: AnonSuite takes a long time to start

**Solution**:
```bash
# Check for slow imports
python -X importtime src/anonsuite.py --version 2>&1 | grep -E "import time|cumulative"

# Disable unnecessary features temporarily
export ANONSUITE_MINIMAL_MODE=1
python src/anonsuite.py --version

# Check system resources
top -p $(pgrep -f anonsuite)
```

### High Memory Usage

**Problem**: Excessive memory consumption

**Solution**:
```bash
# Monitor memory usage
ps aux | grep -E "python|anonsuite"

# Check for memory leaks
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"

# Reduce memory usage
# - Disable unnecessary plugins
# - Use smaller scan timeouts
# - Limit concurrent operations
```

### Network Timeouts

**Problem**: Network operations timing out

**Solution**:
```bash
# Test network connectivity
ping -c 3 8.8.8.8
curl -I https://check.torproject.org

# Increase timeout values in config
nano config/anonsuite.conf
# Update scan_timeout and circuit_timeout values

# Check DNS resolution
nslookup check.torproject.org
dig check.torproject.org
```

## Error Messages

### "Fatal error: EOF when reading a line"

**Cause**: Input stream closed unexpectedly or non-interactive environment

**Solution**:
```bash
# Use non-interactive mode
python src/anonsuite.py --health-check

# Check terminal settings
echo $TERM
tty

# Run with explicit input
echo "0" | python src/anonsuite.py
```

### "ConfigurationError: Required path does not exist"

**Cause**: Missing project directories or incorrect working directory

**Solution**:
```bash
# Ensure you're in the correct directory
pwd
ls -la src/anonsuite.py

# Create missing directories
mkdir -p src/anonymity src/wifi config run log

# Run from correct location
cd /Users/morningstar/Desktop/AnonSuite
python src/anonsuite.py --version
```

### "NetworkInterfaceError: Interface not found"

**Cause**: Specified network interface doesn't exist or isn't available

**Solution**:
```bash
# List available interfaces
ip link show  # Linux
ifconfig      # macOS

# Use correct interface name
python src/anonsuite.py --wifi-scan --wifi-interface en0  # macOS
python src/anonsuite.py --wifi-scan --wifi-interface wlan0  # Linux

# Check interface status
iwconfig wlan0  # Linux only
```

### "ImportError: No module named 'module_name'"

**Cause**: Missing Python dependencies or incorrect Python path

**Solution**:
```bash
# Activate virtual environment
source venv/bin/activate

# Install missing dependencies
pip install -r requirements.txt

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Install specific module
pip install module_name
```

## Getting Help

### Debug Mode

Enable debug mode for more detailed error information:

```bash
# Enable debug logging
python src/anonsuite.py --debug

# Check log files
tail -f log/anonsuite.log

# Verbose output
python src/anonsuite.py --verbose --health-check
```

### Health Check

Run comprehensive health check:

```bash
# Full system health check
python src/anonsuite.py --health-check

# Check specific components
python -c "
import sys
sys.path.append('src')
from config_manager import ConfigManager
config = ConfigManager()
issues = config.validate_config()
print('Errors:', issues['errors'])
print('Warnings:', issues['warnings'])
"
```

### Log Analysis

Check logs for detailed error information:

```bash
# View recent logs
tail -50 log/anonsuite.log

# Search for errors
grep -i error log/anonsuite.log

# Check multitor logs
tail -20 src/anonymity/multitor/multitor.log
```

### System Information

Gather system information for support:

```bash
# System details
uname -a
python3 --version
pip list | grep -E "click|requests|pyyaml"

# Network configuration
ifconfig
netstat -rn

# Service status
ps aux | grep -E "tor|privoxy"
```

### Community Support

If you can't resolve the issue:

1. **Check GitHub Issues**: [AnonSuite Issues](https://github.com/morningstarxcdcode/AnonSuite/issues)
2. **Search Discussions**: [GitHub Discussions](https://github.com/morningstarxcdcode/AnonSuite/discussions)
3. **Create New Issue**: Include:
   - Operating system and version
   - Python version
   - Complete error message
   - Steps to reproduce
   - Output of `--health-check`

### Emergency Recovery

If AnonSuite is completely broken:

```bash
# Reset to clean state
rm -rf venv config/anonsuite.conf
git checkout HEAD -- config/

# Reinstall from scratch
./install.sh

# Or manual reset
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python src/anonsuite.py --config-wizard
```

---

**Remember**: Most issues are related to missing dependencies, incorrect permissions, or configuration problems. The health check command is your first line of defense for diagnosing issues.
