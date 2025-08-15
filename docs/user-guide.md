# AnonSuite User Guide

Complete guide for using AnonSuite's anonymity and WiFi auditing capabilities.

## Table of Contents

- [Getting Started](#getting-started)
- [Anonymity Features](#anonymity-features)
- [WiFi Auditing](#wifi-auditing)
- [Configuration Management](#configuration-management)
- [Plugin System](#plugin-system)
- [Command Line Interface](#command-line-interface)
- [Best Practices](#best-practices)
- [Advanced Usage](#advanced-usage)

## Getting Started

### First Launch

After installation, start AnonSuite with:

```bash
# Interactive menu mode
python src/anonsuite.py

# Or run the configuration wizard first
python src/anonsuite.py --config-wizard
```

### Main Menu Overview

The main menu provides access to all AnonSuite features:

```
┌─ Main Menu ────────────────────────────────────
│ 1. • Anonymity (Tor + Proxy)
│ 2. • WiFi Auditing (Attacks & Scanning)
│ 3. • Configuration Management
│ 4. • System Status & Monitoring
│ 5. • Plugins
│ 6. • Help & Documentation
│ 0. → Back
└───────────────────────────────────────────────
```

### Quick Health Check

Before using AnonSuite, run a health check:

```bash
python src/anonsuite.py --health-check
```

This verifies:
- System dependencies
- Configuration files
- Network connectivity
- Service availability

## Anonymity Features

### Starting Anonymity Services

#### Interactive Mode
1. Select "Anonymity (Tor + Proxy)" from main menu
2. Choose "Start AnonSuite Services"
3. Wait for services to initialize
4. Verify connectivity with "Test Tor Connectivity"

#### Command Line Mode
```bash
# Start all anonymity services
python src/anonsuite.py --start-anonymity

# Check status
python src/anonsuite.py --anonymity-status

# Request new Tor circuit
python src/anonsuite.py --new-circuit
```

### Tor Configuration

#### Basic Settings
- **SOCKS Port**: 9000 (default)
- **Control Port**: 9001 (default)
- **Data Directory**: `src/anonymity/multitor/tor_9000/`

#### Advanced Configuration
```bash
# Edit Tor configuration
nano config/anonsuite.conf

# Key settings:
{
  "anonymity": {
    "tor": {
      "socks_port": 9000,
      "control_port": 9001,
      "circuit_timeout": 60,
      "new_circuit_period": 30
    }
  }
}
```

### Privoxy Integration

Privoxy provides HTTP proxy functionality with filtering:

- **Listen Port**: 8119 (default)
- **Forward to Tor**: 127.0.0.1:9000
- **Configuration**: `/opt/homebrew/etc/privoxy/config`

### Testing Anonymity

#### Connectivity Test
```bash
# Test Tor connectivity
curl --socks5 127.0.0.1:9000 https://check.torproject.org/api/ip

# Test HTTP proxy
curl --proxy 127.0.0.1:8119 https://httpbin.org/ip
```

#### DNS Leak Test
```bash
# Check for DNS leaks
python src/anonsuite.py --anonymity-status
```

## WiFi Auditing

### Network Scanning

#### Interactive Scanning
1. Select "WiFi Auditing" from main menu
2. Choose "Scan for Networks"
3. Select wireless interface
4. Review scan results

#### Command Line Scanning
```bash
# Scan with default interface
python src/anonsuite.py --wifi-scan

# Scan with specific interface
python src/anonsuite.py --wifi-scan --wifi-interface wlan0

# Save results to file
python src/anonsuite.py --wifi-scan --output scan_results.json --format json
```

### Network Analysis

Scan results include security analysis:

- **Open Networks**: No encryption (Very Low security)
- **WEP Networks**: Weak encryption (Low security)
- **WPA Networks**: Moderate encryption (Medium security)
- **WPA2 Networks**: Strong encryption (High security)
- **WPA3 Networks**: Latest encryption (Very High security)

### WPS PIN Attacks

#### Prerequisites
- Target network with WPS enabled
- Captured WPS handshake data
- Pixiewps tool compiled and available

#### Running WPS Attack
```bash
# Interactive mode: WiFi Auditing → WPS PIN Attack
# Command line mode:
python src/anonsuite.py --wps-attack 00:11:22:33:44:55 --wifi-interface wlan0
```

#### Attack Parameters
- **PKE**: Enrollee public key
- **PKR**: Registrar public key
- **E-Hash1**: Enrollee hash-1
- **E-Hash2**: Enrollee hash-2
- **AuthKey**: Authentication session key
- **E-Nonce**: Enrollee nonce

### Rogue Access Point

#### Starting Rogue AP
```bash
# Interactive mode: WiFi Auditing → Start Rogue AP
# Command line mode:
python src/anonsuite.py --start-ap "FreeWiFi" --wifi-interface wlan0
```

#### AP Configuration
- **SSID**: Network name
- **Channel**: WiFi channel (1-11)
- **Security**: Open, WPA2, WPA3
- **Captive Portal**: Optional web portal

#### Stopping Rogue AP
```bash
python src/anonsuite.py --stop-ap
```

## Configuration Management

### Profiles

AnonSuite supports multiple configuration profiles:

#### Creating Profiles
```bash
# Interactive mode: Configuration Management → Create New Profile
# Command line mode:
python src/anonsuite.py --create-profile production
```

#### Switching Profiles
```bash
# List available profiles
python src/anonsuite.py --list-profiles

# Use specific profile
python src/anonsuite.py --profile production
```

#### Profile Operations
```bash
# Export profile
python src/anonsuite.py --export-profile production /path/to/backup.json

# Import profile
python src/anonsuite.py --import-profile imported /path/to/backup.json
```

### Configuration Wizard

The configuration wizard helps set up AnonSuite:

```bash
python src/anonsuite.py --config-wizard
```

Wizard steps:
1. **System Detection**: Identifies OS and available tools
2. **Network Configuration**: Sets up Tor and Privoxy
3. **WiFi Configuration**: Configures wireless interfaces
4. **Security Settings**: Sets security preferences
5. **Profile Creation**: Saves configuration as profile

### Manual Configuration

Edit configuration files directly:

```bash
# Main configuration
nano config/anonsuite.conf

# Tor configuration
nano src/anonymity/multitor/tor_9000/torrc

# Privoxy configuration
sudo nano /opt/homebrew/etc/privoxy/config
```

## Plugin System

### Available Plugins

List installed plugins:
```bash
python src/anonsuite.py --list-plugins
```

### Running Plugins

#### Interactive Mode
1. Select "Plugins" from main menu
2. Choose plugin from list
3. Follow plugin-specific instructions

#### Command Line Mode
```bash
python src/anonsuite.py --run-plugin "Network Info Plugin"
```

### Creating Custom Plugins

Create a new plugin file in the `plugins/` directory:

```python
#!/usr/bin/env python3
"""
Custom AnonSuite Plugin
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from anonsuite import AnonSuitePlugin

class CustomPlugin(AnonSuitePlugin):
    def __init__(self, cli_instance):
        super().__init__(cli_instance)
        self.name = "Custom Plugin"
        self.version = "1.0.0"
        self.description = "My custom plugin"
    
    def run(self, *args, **kwargs):
        print(f"Running {self.name}...")
        # Plugin functionality here
        return {"status": "success", "message": "Plugin executed"}
```

## Command Line Interface

### Basic Commands

```bash
# Version information
python src/anonsuite.py --version

# Help and usage
python src/anonsuite.py --help

# Health check
python src/anonsuite.py --health-check
```

### Anonymity Commands

```bash
# Start/stop anonymity services
python src/anonsuite.py --start-anonymity
python src/anonsuite.py --stop-anonymity

# Check status and request new circuit
python src/anonsuite.py --anonymity-status
python src/anonsuite.py --new-circuit
```

### WiFi Commands

```bash
# Network scanning
python src/anonsuite.py --wifi-scan
python src/anonsuite.py --wifi-scan --wifi-interface wlan0

# Rogue AP operations
python src/anonsuite.py --start-ap "TestAP"
python src/anonsuite.py --stop-ap

# WPS attacks
python src/anonsuite.py --wps-attack 00:11:22:33:44:55
```

### Configuration Commands

```bash
# Profile management
python src/anonsuite.py --list-profiles
python src/anonsuite.py --create-profile test
python src/anonsuite.py --profile test

# Import/export
python src/anonsuite.py --export-profile default backup.json
python src/anonsuite.py --import-profile restored backup.json
```

### Output Options

```bash
# Save output to file
python src/anonsuite.py --wifi-scan --output results.json

# Different output formats
python src/anonsuite.py --wifi-scan --format json
python src/anonsuite.py --wifi-scan --format csv
python src/anonsuite.py --wifi-scan --format text

# Disable colors
python src/anonsuite.py --no-color
```

## Best Practices

### Security

1. **Verify Anonymity**: Always test Tor connectivity before sensitive operations
2. **Use Strong Passwords**: Configure strong passwords for rogue APs
3. **Monitor Logs**: Regularly check logs for suspicious activity
4. **Update Regularly**: Keep AnonSuite and dependencies updated

### Network Testing

1. **Authorization**: Only test networks you own or have permission to test
2. **Documentation**: Document all testing activities
3. **Responsible Disclosure**: Report vulnerabilities responsibly
4. **Legal Compliance**: Follow local laws and regulations

### Performance

1. **Resource Monitoring**: Monitor CPU and memory usage
2. **Network Bandwidth**: Be aware of bandwidth consumption
3. **Circuit Rotation**: Regularly rotate Tor circuits
4. **Clean Shutdown**: Always stop services properly

### Troubleshooting

1. **Health Checks**: Run regular health checks
2. **Log Analysis**: Check logs for errors and warnings
3. **Configuration Validation**: Validate configuration files
4. **Service Status**: Monitor service status

## Advanced Usage

### Custom Tor Configuration

Edit Tor configuration for advanced settings:

```bash
nano src/anonymity/multitor/tor_9000/torrc
```

Advanced options:
```
# Exit node country selection
ExitNodes {us},{de},{nl}
StrictNodes 1

# Bridge configuration
UseBridges 1
Bridge obfs4 [bridge_address]

# Hidden service
HiddenServiceDir /path/to/hidden_service/
HiddenServicePort 80 127.0.0.1:8080
```

### Multiple Tor Instances

Run multiple Tor instances for circuit isolation:

```bash
# Start additional Tor instance
./src/anonymity/multitor/multitor --socks-port 9002 --control-port 9003
```

### Custom WiFi Attacks

Implement custom WiFi attack scripts:

```python
from wifi.wifi_scanner import WiFiScanner
from wifi.pixiewps_wrapper import PixiewpsWrapper

# Custom attack workflow
scanner = WiFiScanner()
networks = scanner.scan_networks()

# Filter for WPS-enabled networks
wps_networks = [n for n in networks if 'WPS' in n.get('encryption', '')]

# Automated attack on multiple targets
for network in wps_networks:
    # Implement custom attack logic
    pass
```

### Automation Scripts

Create automation scripts for common tasks:

```bash
#!/bin/bash
# automated_scan.sh

# Start anonymity services
python src/anonsuite.py --start-anonymity

# Wait for services to start
sleep 10

# Perform WiFi scan
python src/anonsuite.py --wifi-scan --output "scan_$(date +%Y%m%d_%H%M%S).json"

# Stop services
python src/anonsuite.py --stop-anonymity
```

### Integration with Other Tools

Integrate AnonSuite with external tools:

```python
# Example: Integration with Nmap
import subprocess
import json

# Get scan results from AnonSuite
result = subprocess.run([
    'python', 'src/anonsuite.py', '--wifi-scan', '--format', 'json'
], capture_output=True, text=True)

networks = json.loads(result.stdout)

# Use results with Nmap
for network in networks:
    if network['encryption'] == 'Open':
        # Scan open networks with Nmap
        subprocess.run(['nmap', '-sn', f"{network['gateway']}/24"])
```

---

**Need Help?** Check the [Troubleshooting Guide](troubleshooting.md) or visit our [GitHub Discussions](https://github.com/morningstarxcdcode/AnonSuite/discussions).
