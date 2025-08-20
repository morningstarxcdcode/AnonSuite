# AnonSuite - Unified Security Toolkit for the Pragmatic Engineer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Security](https://img.shields.io/badge/security-focused-brightgreen.svg)](./SECURITY_MODEL.md)
[![Real-World Ready](https://img.shields.io/badge/real--world-ready-brightgreen.svg)](./REAL_WORLD_USAGE.md)

**AnonSuite** is a command-line toolkit I built after years of frustration with fragmented security tools. It pragmatically integrates battle-tested open-source components into a unified platform for multi-layered traffic obfuscation and network security auditing. This reflects a real-world development approach - balancing robust engineering with maintainable code that actually works in production.

## 🚀 Is This Actually Usable in Real Life?

**Yes, absolutely!** You can verify this immediately:

```bash
# Test it right now (works immediately after cloning)
git clone https://github.com/morningstarxcdcode/AnonSuite.git
cd AnonSuite
python src/anonsuite/main.py --demo
python src/anonsuite/main.py --health-check
```

**Core functionality works immediately** - no installation required. For full features, AnonSuite will tell you exactly what dependencies you need.

📖 **[Complete Real-World Usage Guide](./REAL_WORLD_USAGE.md)** | 🧪 **[Run Validation Test](./validate_usability.sh)**

## 🎯 Real-World Validation

**Immediate Usability Test** (works right after cloning):
```bash
./validate_usability.sh  # Comprehensive validation
```

**Quick Verification** (3 commands):
```bash
python src/anonsuite/main.py --version    # ✓ Version info
python src/anonsuite/main.py --demo       # ✓ Feature demo  
python src/anonsuite/main.py --health-check  # ✓ System status
```

**Production Use Cases**:
- **Security Professionals**: Network assessment and anonymity management
- **Students/Researchers**: Interactive learning and concept exploration  
- **Penetration Testers**: WiFi security testing and configuration management

## Key Features

### Network Anonymization (Core Focus)
- **Multi-Tor Orchestration**: Manages multiple Tor instances for circuit isolation and traffic routing
- **Proxy Chaining**: Integrates Privoxy and HAProxy for flexible proxy configurations  
- **Robust Logging**: Detailed, timestamped logs for operational insight and debugging

### WiFi Security Auditing (Integrated)
- **Network Reconnaissance**: Comprehensive WiFi scanning and analysis
- **WPS PIN Recovery**: Pixiewps integration for WPS vulnerability testing
- **Rogue AP Framework**: WiFiPumpkin3 integration for access point simulation

### Pragmatic Engineering
- **Modular Design**: Built for extensibility and maintainability
- **Absolute Path Reliance**: Ensures binary discovery and execution reliability across environments
- **Human-Coded Aesthetic**: Code and documentation reflect natural, iterative development process

## Quick Start

### Prerequisites
- **macOS or Linux-based system**
- **Python 3.8 or higher**
- **sudo privileges** for certain network operations
- **Homebrew** (macOS) or your system's package manager (Linux) for external dependencies

### External Dependencies
AnonSuite orchestrates external binaries. Install them via Homebrew (macOS) or your system's package manager:

```bash
# Install Tor
brew install tor

# Install Privoxy  
brew install privoxy

# Install HAProxy
brew install haproxy

# Install pidof (part of proctools on macOS)
brew install proctools
```

### Installation

```bash
# Clone the repository
git clone https://github.com/morningstarxcdcode/AnonSuite.git
cd AnonSuite

# Make multitor scripts executable
chmod +x src/anonymity/multitor/multitor \
         src/anonymity/multitor/__init__ \
         src/anonymity/multitor/CreateTorProcess \
         src/anonymity/multitor/CreateProxyProcess
```

### Initial Setup & Troubleshooting for multitor

**Important:** multitor requires specific permissions and port availability. Follow these steps carefully:

1. **Fix Tor Data Directory Ownership:** Tor needs its data directory to be owned by the user it runs as. If previous runs created it as root, you must fix ownership:
   ```bash
   sudo chown -R $USER ~/Desktop/AnonSuite/src/anonymity/multitor/tor_9000
   # Repeat for any other tor_* directories if they exist
   ```

2. **Resolve Privoxy Port Conflict:** Privoxy's default port (8118) might be in use. You need to:
   - **Kill any conflicting process:**
     ```bash
     lsof -i :8118
     # If a process is listed, kill it (replace <PID> with the actual process ID)
     sudo kill <PID>
     ```
   - **Change Privoxy's listening port:** Edit its configuration file:
     ```bash
     sudo nano /opt/homebrew/etc/privoxy/config
     # Find the line: listen-address 127.0.0.1:8118
     # Change 8118 to an unused port, e.g., 8119:
     # listen-address 127.0.0.1:8119
     # Save and exit (CTRL+O, Enter, CTRL+X)
     ```

### Running multitor

Once prerequisites and initial setup are complete, run multitor with your actual username. The output will be logged live to your terminal and saved to multitor.log.

```bash
# Replace <YOUR_USERNAME> with your actual system username
sudo /Users/$USER/Desktop/AnonSuite/src/anonymity/multitor/multitor \
  --user $USER \
  --socks-port 9000 \
  --control-port 9001 \
  --proxy privoxy \
  --haproxy yes
```

## Project Structure

```
AnonSuite/
├── src/                    # Core application code
│   ├── anonsuite.py       # Main CLI interface
│   ├── config_manager.py  # Configuration management system
│   ├── anonymity/         # Tor and proxy modules
│   │   └── multitor/      # Core multitor scripts and helpers
│   │       ├── multitor
│   │       ├── __init__
│   │       ├── CreateTorProcess
│   │       ├── CreateProxyProcess
│   │       ├── helpers
│   │       ├── settings
│   │       └── multitor.log # Operational logs
│   └── wifi/              # WiFi auditing tools
│       ├── pixiewps_wrapper.py
│       ├── wifipumpkin_wrapper.py
│       └── wifi_scanner.py
├── tests/                 # Comprehensive test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── security/          # Security tests
├── docs/                  # Project documentation
│   ├── installation.md    # Installation guide
│   ├── user-guide.md      # User documentation
│   └── troubleshooting.md # Troubleshooting guide
├── config/                # Configuration files
├── plugins/               # Plugin system
├── run/                   # Runtime files and logs
├── .github/               # GitHub Actions CI/CD workflows
│   └── workflows/
│       └── ci.yml         # Automated testing pipeline
├── .env.example           # Environment variables template
├── architect-state.json   # Project state tracking
├── pyproject.toml         # Python project configuration
└── README.md              # You are here
```

## Usage

### Interactive Mode
```bash
# Start the interactive menu
python src/anonsuite.py
```

### Command Line Mode
```bash
# Check version and health
python src/anonsuite.py --version
python src/anonsuite.py --health-check

# Anonymity operations
python src/anonsuite.py --start-anonymity
python src/anonsuite.py --anonymity-status
python src/anonsuite.py --new-circuit

# WiFi operations
python src/anonsuite.py --wifi-scan
python src/anonsuite.py --wifi-scan --wifi-interface wlan0

# Configuration management
python src/anonsuite.py --config-wizard
python src/anonsuite.py --list-profiles
python src/anonsuite.py --create-profile production

# Plugin system
python src/anonsuite.py --list-plugins
python src/anonsuite.py --run-plugin "Network Info Plugin"
```

## Testing & Quality Assurance

The project includes a comprehensive testing framework:

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests  
pytest tests/security/      # Security tests

# Run with coverage
pytest --cov=src --cov-report=html
```

## CI/CD Pipeline

A GitHub Actions workflow ensures code quality and consistency:
- **Linting**: ruff check and ruff format --check
- **Type Checking**: mypy src/
- **Security Scanning**: bandit and safety
- **Testing**: pytest across multiple Python versions
- **Multi-OS Support**: Ubuntu and macOS

## Documentation

- **[Installation Guide](./docs/installation.md)**: Comprehensive setup instructions
- **[User Guide](./docs/user-guide.md)**: Detailed usage documentation
- **[Troubleshooting](./docs/troubleshooting.md)**: Common issues and solutions
- **multitor.log**: Detailed operational logs for debugging

## Security & Legal

### Ethical Use
This toolkit is designed for:
- [x] Authorized penetration testing
- [x] Security research and education
- [x] Network security assessment
- [x] Compliance validation

### Legal Disclaimer
- **Unauthorized use is prohibited**
- **Always obtain explicit permission**
- **Respect local laws and regulations**
- **No warranty or liability**

The developers are not responsible for misuse of this software. Users must ensure compliance with applicable laws and obtain proper authorization before conducting any security assessments.

## Contributing

We welcome contributions! The project follows standard open-source practices:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure all tests pass
5. Submit a pull request

See our [Contributing Guide](./docs/contributing.md) for detailed guidelines.

## Support & Contact

### Author
- **Developer**: morningstarxcdcode
- **LinkedIn**: [Sourav Rajak](https://www.linkedin.com/in/sourav-rajak-6294682b2)
- **GitHub**: [@morningstarxcdcode](https://github.com/morningstarxcdcode)

### Project Repository
- **Repository**: [AnonSuite on GitHub](https://github.com/morningstarxcdcode/AnonSuite)
- **Issues**: Report bugs and request features at [GitHub Issues](https://github.com/morningstarxcdcode/AnonSuite/issues)
- **Discussions**: Join community discussions at [GitHub Discussions](https://github.com/morningstarxcdcode/AnonSuite/discussions)

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## Acknowledgments

Special thanks to the developers of the integrated tools:
- [trimstray](https://github.com/trimstray) for multitor
- [P0cL4bs](https://github.com/P0cL4bs) for wifipumpkin3
- [wiire-a](https://github.com/wiire-a) for pixiewps

---

**Important**: This tool is for authorized security testing only. Always ensure you have proper permission before conducting any security assessments. The developers assume no liability for misuse of this software.
