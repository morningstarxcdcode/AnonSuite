# AnonSuite Installation Guide

This guide provides comprehensive instructions for installing AnonSuite on various operating systems.

## Table of Contents

- [System Requirements](#system-requirements)
- [Quick Installation](#quick-installation)
- [Detailed Installation](#detailed-installation)
- [Post-Installation Setup](#post-installation-setup)
- [Troubleshooting](#troubleshooting)
- [Uninstallation](#uninstallation)

## System Requirements

### Minimum Requirements
- **Operating System**: macOS 10.15+, Ubuntu 18.04+, Debian 10+, or compatible Linux distribution
- **Python**: 3.8 or higher
- **Memory**: 2GB RAM minimum, 4GB recommended
- **Storage**: 1GB free disk space
- **Network**: Internet connection for initial setup and updates

### Recommended Requirements
- **Operating System**: macOS 12+, Ubuntu 20.04+
- **Python**: 3.11 or higher
- **Memory**: 8GB RAM
- **Storage**: 5GB free disk space
- **Privileges**: sudo/administrator access for system-level operations

## Quick Installation

### macOS (Homebrew)

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install system dependencies
brew install tor privoxy python@3.11

# Clone and setup AnonSuite
git clone https://github.com/morningstarxcdcode/AnonSuite.git
cd AnonSuite
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run initial setup
python src/anonsuite.py --config-wizard
```

### Ubuntu/Debian

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y tor privoxy python3 python3-pip python3-venv git wireless-tools net-tools

# Clone and setup AnonSuite
git clone https://github.com/morningstarxcdcode/AnonSuite.git
cd AnonSuite
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run initial setup
python src/anonsuite.py --config-wizard
```

## Detailed Installation

### Step 1: System Dependencies

#### macOS
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required packages
brew install tor privoxy python@3.11 git
brew install --cask wireshark  # Optional, for advanced network analysis
```

#### Ubuntu/Debian
```bash
# Update package lists
sudo apt update

# Install core dependencies
sudo apt install -y \
    tor \
    privoxy \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    wireless-tools \
    net-tools \
    build-essential

# Install optional dependencies
sudo apt install -y \
    wireshark \
    aircrack-ng \
    reaver \
    pixiewps
```

#### Fedora/CentOS/RHEL
```bash
# Install EPEL repository (CentOS/RHEL)
sudo yum install -y epel-release  # CentOS 7
sudo dnf install -y epel-release  # CentOS 8+/Fedora

# Install dependencies
sudo dnf install -y \
    tor \
    privoxy \
    python3 \
    python3-pip \
    python3-devel \
    git \
    wireless-tools \
    net-tools \
    gcc \
    gcc-c++
```

### Step 2: Download AnonSuite

#### Option A: Git Clone (Recommended)
```bash
# Clone the repository
git clone https://github.com/morningstarxcdcode/AnonSuite.git
cd AnonSuite

# Verify the download
ls -la
```

#### Option B: Download Release Archive
```bash
# Download latest release
curl -L https://github.com/morningstarxcdcode/AnonSuite/archive/refs/heads/main.zip -o AnonSuite.zip

# Extract archive
unzip AnonSuite.zip
cd AnonSuite-main
```

### Step 3: Python Environment Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

### Step 4: WiFi Tools Setup

#### Pixiewps (WPS PIN Recovery)
```bash
# Navigate to pixiewps directory
cd src/wifi/pixiewps

# Compile pixiewps
make

# Verify compilation
./pixiewps -h
```

#### WiFiPumpkin3 (Rogue AP Framework)
```bash
# Install PyQt5 dependencies
pip install PyQt5 PyQt5-tools

# Install additional WiFi dependencies
pip install scapy netfilterqueue

# Test WiFiPumpkin3
cd src/wifi/wifipumpkin3
python3 -m wifipumpkin3 --help
```

### Step 5: Configuration

```bash
# Run configuration wizard
python src/anonsuite.py --config-wizard

# Or manually create configuration
mkdir -p config
cp config/anonsuite.conf.example config/anonsuite.conf

# Edit configuration file
nano config/anonsuite.conf
```

## Post-Installation Setup

### 1. Verify Installation

```bash
# Check AnonSuite version
python src/anonsuite.py --version

# Run health check
python src/anonsuite.py --health-check

# List available profiles
python src/anonsuite.py --list-profiles
```

### 2. Configure Tor

```bash
# Check Tor configuration
sudo nano /opt/homebrew/etc/tor/torrc  # macOS
sudo nano /etc/tor/torrc               # Linux

# Add recommended settings
echo "ControlPort 9001" | sudo tee -a /etc/tor/torrc
echo "CookieAuthentication 1" | sudo tee -a /etc/tor/torrc
```

### 3. Configure Privoxy

```bash
# Edit Privoxy configuration
sudo nano /opt/homebrew/etc/privoxy/config  # macOS
sudo nano /etc/privoxy/config               # Linux

# Ensure these lines are present:
# listen-address 127.0.0.1:8119
# forward-socks5 / 127.0.0.1:9000 .
```

### 4. Set Up Permissions

```bash
# Make scripts executable
chmod +x src/anonymity/multitor/multitor
chmod +x src/anonymity/multitor/__init__
chmod +x src/anonymity/multitor/CreateTorProcess
chmod +x src/anonymity/multitor/CreateProxyProcess

# Set up log directories
mkdir -p log run
chmod 755 log run
```

### 5. Test Core Functionality

```bash
# Test anonymity services
python src/anonsuite.py --start-anonymity

# Test WiFi scanning (requires wireless interface)
python src/anonsuite.py --wifi-scan

# Test plugin system
python src/anonsuite.py --list-plugins
```

## Troubleshooting

### Common Issues

#### 1. Permission Denied Errors
```bash
# Fix ownership issues
sudo chown -R $USER:$USER ~/Desktop/AnonSuite

# Fix script permissions
chmod +x src/anonymity/multitor/*
```

#### 2. Tor Connection Issues
```bash
# Check Tor status
sudo systemctl status tor  # Linux
brew services list | grep tor  # macOS

# Restart Tor service
sudo systemctl restart tor  # Linux
brew services restart tor  # macOS
```

#### 3. Python Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

#### 4. WiFi Tools Not Working
```bash
# Check wireless interface
iwconfig  # Linux
system_profiler SPAirPortDataType  # macOS

# Install missing wireless tools
sudo apt install wireless-tools aircrack-ng  # Ubuntu/Debian
```

#### 5. Port Conflicts
```bash
# Check for port conflicts
lsof -i :9000  # Tor SOCKS port
lsof -i :9001  # Tor control port
lsof -i :8119  # Privoxy port

# Kill conflicting processes
sudo kill <PID>
```

### Getting Help

If you encounter issues not covered here:

1. **Check the logs**: `tail -f log/anonsuite.log`
2. **Run health check**: `python src/anonsuite.py --health-check`
3. **Enable debug mode**: `python src/anonsuite.py --debug`
4. **Check GitHub Issues**: [AnonSuite Issues](https://github.com/morningstarxcdcode/AnonSuite/issues)
5. **Join Discussions**: [GitHub Discussions](https://github.com/morningstarxcdcode/AnonSuite/discussions)

## Uninstallation

### Complete Removal

```bash
# Stop all services
python src/anonsuite.py --stop-anonymity

# Remove AnonSuite directory
cd ..
rm -rf AnonSuite

# Remove system dependencies (optional)
brew uninstall tor privoxy  # macOS
sudo apt remove tor privoxy  # Ubuntu/Debian

# Clean up configuration files
rm -rf ~/.config/anonsuite
rm -rf ~/.local/share/anonsuite
```

### Keep Configuration

```bash
# Remove only the application
cd ..
rm -rf AnonSuite

# Configuration files remain in:
# ~/.config/anonsuite/
# ~/.local/share/anonsuite/
```

## Security Considerations

### File Permissions
- Ensure configuration files are not world-readable
- Keep private keys and sensitive data secure
- Regularly update dependencies

### Network Security
- Use AnonSuite only on trusted networks
- Verify Tor connectivity before sensitive operations
- Monitor for DNS leaks

### Legal Compliance
- Only use on networks you own or have permission to test
- Comply with local laws and regulations
- Obtain proper authorization for security testing

---

**Next Steps**: After installation, see the [User Guide](user-guide.md) for detailed usage instructions.
