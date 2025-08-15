# Contributing to AnonSuite

Thank you for your interest in contributing to AnonSuite! This guide will help you get started with contributing to our security toolkit project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Security Considerations](#security-considerations)
- [Submitting Changes](#submitting-changes)
- [Community](#community)

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

Examples of behavior that contributes to creating a positive environment include:

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by contacting the project team. All complaints will be reviewed and investigated promptly and fairly.

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Python 3.8 or higher
- Git for version control
- Basic understanding of security concepts
- Familiarity with command-line tools

### Areas for Contribution

We welcome contributions in several areas:

1. **Core Features**: Anonymity tools, WiFi auditing, CLI improvements
2. **Plugin Development**: Extending functionality through plugins
3. **Testing**: Unit tests, integration tests, security tests
4. **Documentation**: User guides, API documentation, tutorials
5. **Bug Fixes**: Resolving issues and improving stability
6. **Security**: Vulnerability fixes and security enhancements

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/AnonSuite.git
cd AnonSuite

# Add upstream remote
git remote add upstream https://github.com/morningstarxcdcode/AnonSuite.git
```

### 2. Set Up Development Environment

```bash
# Run the installation script
./install.sh

# Or manual setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

### 3. Install Pre-commit Hooks

```bash
# Install pre-commit hooks for code quality
pre-commit install

# Test the hooks
pre-commit run --all-files
```

### 4. Verify Setup

```bash
# Run health check
python src/anonsuite.py --health-check

# Run tests
pytest tests/

# Check code quality
ruff check src/
mypy src/
```

## Contributing Guidelines

### Issue Reporting

Before creating a new issue:

1. **Search existing issues** to avoid duplicates
2. **Use the issue templates** provided
3. **Include system information** (OS, Python version, etc.)
4. **Provide reproduction steps** for bugs
5. **Include logs and error messages**

### Feature Requests

When proposing new features:

1. **Explain the use case** and problem it solves
2. **Consider security implications** of the feature
3. **Discuss implementation approach** if you have ideas
4. **Check if it fits the project scope** (security toolkit)

### Pull Request Process

1. **Create a feature branch** from `develop`
2. **Make focused commits** with clear messages
3. **Add tests** for new functionality
4. **Update documentation** as needed
5. **Ensure all checks pass** (tests, linting, security)
6. **Request review** from maintainers

## Code Standards

### Python Style Guide

We follow PEP 8 with some project-specific conventions:

```python
# Good: Clear, descriptive names
def scan_wifi_networks(interface: str, timeout: int = 30) -> List[Dict]:
    """Scan for available WiFi networks on specified interface."""
    pass

# Good: Type hints for better code clarity
class WiFiScanner:
    def __init__(self, config: ConfigManager) -> None:
        self.config = config
        self.results: List[Dict] = []

# Good: Docstrings for public methods
def analyze_network_security(network_data: Dict) -> SecurityAssessment:
    """
    Analyze network security based on encryption and configuration.
    
    Args:
        network_data: Dictionary containing network information
        
    Returns:
        SecurityAssessment object with vulnerability analysis
        
    Raises:
        NetworkAnalysisError: If network data is invalid
    """
    pass
```

### Code Organization

```python
# File structure should follow this pattern:
#!/usr/bin/env python3
"""
Module docstring explaining purpose and usage.
"""

# Standard library imports
import os
import sys
from typing import Dict, List, Optional

# Third-party imports
import requests
import yaml

# Local imports
from config_manager import ConfigManager
from .exceptions import AnonSuiteError

# Constants
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# Classes and functions...
```

### Error Handling

```python
# Good: Specific exception types
class NetworkScanError(AnonSuiteError):
    """Raised when network scanning fails."""
    pass

# Good: Proper exception handling
def scan_network(interface: str) -> List[Dict]:
    try:
        result = subprocess.run(['iwlist', interface, 'scan'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise NetworkScanError(f"Scan failed: {result.stderr}")
        return parse_scan_results(result.stdout)
    except subprocess.TimeoutExpired:
        raise NetworkScanError(f"Scan timed out on interface {interface}")
    except Exception as e:
        raise NetworkScanError(f"Unexpected error during scan: {e}")
```

### Security Considerations

```python
# Good: Input validation
def validate_interface_name(interface: str) -> bool:
    """Validate network interface name to prevent injection attacks."""
    if not interface or not isinstance(interface, str):
        return False
    # Only allow alphanumeric characters and common interface patterns
    import re
    return bool(re.match(r'^[a-zA-Z0-9]+$', interface))

# Good: Secure file operations
def save_config(config_data: Dict, config_path: str) -> None:
    """Save configuration with secure file permissions."""
    import stat
    
    # Create file with restricted permissions
    with open(config_path, 'w', opener=lambda path, flags: 
              os.open(path, flags, stat.S_IRUSR | stat.S_IWUSR)) as f:
        json.dump(config_data, f, indent=2)
```

## Testing Requirements

### Test Categories

1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test component interactions
3. **Security Tests**: Test for vulnerabilities and security issues
4. **End-to-End Tests**: Test complete workflows

### Writing Tests

```python
# tests/unit/test_wifi_scanner.py
import pytest
from unittest.mock import Mock, patch
from wifi.wifi_scanner import WiFiScanner

class TestWiFiScanner:
    def test_scanner_initialization(self):
        """Test WiFi scanner initializes correctly."""
        scanner = WiFiScanner()
        assert scanner is not None
        assert hasattr(scanner, 'scan_networks')
    
    @patch('subprocess.run')
    def test_network_scanning(self, mock_run):
        """Test network scanning with mocked system calls."""
        # Mock successful scan
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Cell 01 - Address: 00:11:22:33:44:55\n          ESSID:\"TestNetwork\""
        )
        
        scanner = WiFiScanner()
        networks = scanner.scan_networks('wlan0')
        
        assert isinstance(networks, list)
        mock_run.assert_called_once()
    
    def test_invalid_interface_handling(self):
        """Test handling of invalid interface names."""
        scanner = WiFiScanner()
        
        # Should handle invalid interfaces gracefully
        with pytest.raises(ValueError):
            scanner.scan_networks('invalid; rm -rf /')
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/security/

# Run with coverage
pytest --cov=src --cov-report=html

# Run security-specific tests
pytest -m security
```

## Security Considerations

### Security Review Process

All contributions undergo security review:

1. **Automated Security Scanning**: Bandit, Safety, and other tools
2. **Manual Code Review**: Focus on security implications
3. **Penetration Testing**: For significant security features
4. **Vulnerability Disclosure**: Responsible disclosure process

### Security Guidelines

```python
# DO: Validate all inputs
def process_user_input(user_data: str) -> str:
    if not isinstance(user_data, str):
        raise ValueError("Input must be string")
    
    # Sanitize input
    sanitized = re.sub(r'[^\w\s-]', '', user_data)
    return sanitized[:100]  # Limit length

# DON'T: Execute user input directly
def bad_example(command: str):
    os.system(command)  # NEVER DO THIS

# DO: Use subprocess with proper validation
def execute_safe_command(interface: str):
    if not validate_interface_name(interface):
        raise ValueError("Invalid interface name")
    
    subprocess.run(['iwconfig', interface], check=True)
```

### Sensitive Data Handling

```python
# DO: Handle sensitive data securely
import secrets
from cryptography.fernet import Fernet

def generate_secure_token() -> str:
    """Generate cryptographically secure token."""
    return secrets.token_urlsafe(32)

def encrypt_sensitive_data(data: str, key: bytes) -> bytes:
    """Encrypt sensitive data before storage."""
    f = Fernet(key)
    return f.encrypt(data.encode())

# DON'T: Log sensitive information
logger.info(f"Processing password: {password}")  # BAD

# DO: Log safely
logger.info("Processing authentication data")  # GOOD
```

## Submitting Changes

### Commit Message Format

Use conventional commit format:

```
type(scope): brief description

Detailed explanation of changes if needed.

Fixes #123
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `security`: Security-related changes

Examples:
```
feat(wifi): add WPA3 network detection support

Implements detection and analysis of WPA3 encrypted networks
in the WiFi scanner module. Includes security assessment
updates for WPA3 networks.

Fixes #45

security(auth): fix potential command injection in interface validation

Adds proper input sanitization to prevent command injection
attacks through network interface names.

Fixes #67
```

### Pull Request Checklist

Before submitting a pull request:

- [ ] Code follows project style guidelines
- [ ] All tests pass locally
- [ ] New tests added for new functionality
- [ ] Documentation updated if needed
- [ ] Security implications considered
- [ ] Commit messages follow convention
- [ ] No sensitive data in commits
- [ ] Pre-commit hooks pass

### Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and security scans
2. **Code Review**: Maintainers review code quality and security
3. **Testing**: Manual testing of new features
4. **Documentation Review**: Ensure documentation is accurate
5. **Security Review**: Additional security review for sensitive changes

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and community discussion
- **Security Issues**: Use private security reporting for vulnerabilities

### Getting Help

- **Documentation**: Check docs/ directory first
- **Troubleshooting**: See docs/troubleshooting.md
- **Community**: Ask questions in GitHub Discussions
- **Mentorship**: Maintainers are happy to help new contributors

### Recognition

Contributors are recognized through:

- **Contributors List**: Added to README.md
- **Release Notes**: Contributions mentioned in releases
- **GitHub Recognition**: Contributor badges and statistics

## Development Workflow

### Branching Strategy

```bash
# Main branches
main        # Production-ready code
develop     # Integration branch for features

# Feature branches
feature/wifi-wpa3-support
fix/config-loading-issue
security/input-validation
docs/api-reference-update
```

### Release Process

1. **Feature Development**: Work in feature branches
2. **Integration**: Merge to develop branch
3. **Testing**: Comprehensive testing on develop
4. **Release Preparation**: Create release branch
5. **Final Testing**: Security audit and final tests
6. **Release**: Merge to main and tag version

### Maintenance

- **Bug Fixes**: Priority for security and critical bugs
- **Dependencies**: Regular updates for security patches
- **Documentation**: Keep documentation current with code changes
- **Community**: Respond to issues and discussions promptly

---

Thank you for contributing to AnonSuite! Your contributions help make security tools more accessible and effective for the community.
