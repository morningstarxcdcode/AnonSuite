# AnonSuite Architecture Document

## 1. Introduction
This document outlines the existing architecture of AnonSuite, a command-line interface (CLI) toolkit designed to enhance online anonymity and security. It integrates various open-source tools to provide multi-layered traffic obfuscation and network security auditing capabilities.

## 2. Core Components & Technologies
AnonSuite is primarily built using **Python 3.x** and orchestrates several external tools:

- **Tor:** The Onion Router, used for anonymous communication over the internet.
- **Polipo:** A caching web proxy, potentially used in proxy chains.
- **Privoxy:** A non-caching web proxy with advanced filtering capabilities, often used for privacy enhancement.
- **HAProxy:** A high-performance TCP/HTTP load balancer and proxy, used here for managing proxy chains and traffic routing.
- **Multitor:** (Identified from logs) A component within AnonSuite responsible for managing multiple Tor instances and proxy chains.
- **Pixiewps:** A tool for auditing WPS-enabled networks.
- **Wifipumpkin3:** A framework for rogue access point attacks and WiFi security auditing.

## 3. System Structure & Flow

### 3.1. Overall Design Philosophy
AnonSuite follows a modular, CLI-driven design. Its primary function is to act as an orchestrator, configuring and launching external tools based on user commands. The core logic resides in `src/anonsuite.py` and related Python modules.

### 3.2. Key Modules & Their Responsibilities
- **`src/anonsuite.py`:** The main entry point for the application, handling command-line argument parsing and dispatching commands to relevant sub-modules.
- **`src/anonymity/multitor/`:** This directory likely contains the Python code for the `multitor` component, responsible for:
    - Spawning and managing multiple Tor processes.
    - Configuring and chaining proxies (Polipo, Privoxy, HAProxy).
    - Routing network traffic through the configured anonymity layers.
- **`src/wifi/`:** Contains scripts and potentially Python wrappers for WiFi-related tools:
    - `compile_pixiewps.sh`, `run_pixiewps.sh`: Scripts for Pixiewps management.
    - `run_wifipumpkin.sh`: Script for Wifipumpkin3 execution.

### 3.3. Interaction with External Tools
AnonSuite interacts with external tools primarily through shell commands (as evidenced by the `Makefile` and the nature of tools like Pixiewps and Wifipumpkin3). Configuration files for proxies (e.g., `etc/templates/`) are used as templates and likely modified dynamically before launching the proxy services.

## 4. Data Model & Configuration

### 4.1. Configuration Files
- **`etc/templates/`:** Contains template configuration files for proxies (e.g., `haproxy-template.cfg`, `polipo-template.cfg`, `privoxy-template.cfg`). These are likely read, modified with dynamic parameters (ports, routes), and then written to temporary locations before the proxies are launched.
- **`.env.example`:** Indicates the use of environment variables for sensitive or configurable parameters, promoting secure practices.

### 4.2. Persistent Data
Given its CLI nature, AnonSuite likely has minimal persistent data. Any state management would primarily be for temporary operational data (e.g., process IDs of running proxies, current network configurations) rather than complex databases.

## 5. User Interface / User Experience (UI/UX)

### 5.1. Command-Line Interface
AnonSuite provides a pure CLI experience. Users interact with the application by executing commands and providing arguments. Output is typically text-based, displayed directly in the terminal.

## 6. Observability

### 6.1. Logging
- The presence of `log/multitor.20250811.log` indicates that the `multitor` component, and likely other parts of the application, generate logs for debugging and operational monitoring. Logs appear to include `INFO`, `DEBUG`, `WARNING`, and `ERROR` levels.

## 7. Deployment & Environment Strategy

### 7.1. Local Installation
Deployment is primarily local, as indicated by the `Makefile`'s `install` target, which handles dependency installation and compilation of tools like Pixiewps and Wifipumpkin3.

### 7.2. Cross-Platform Compatibility
The `README.md` mentions cross-platform compatibility, suggesting that the Python codebase and shell scripts are designed to run on various Unix-like operating systems (e.g., Linux, macOS).

## 8. Security Model

### 8.1. Core Security Principles
AnonSuite's core purpose is to enhance user security and anonymity. This implies:
- **Traffic Obfuscation:** Hiding user's real IP address and location.
- **Encryption:** Leveraging tools like Tor for encrypted communication.
- **Privacy:** Minimizing data leakage and tracking.

### 8.2. Identified Security-Related Components
- **Tor:** Provides strong anonymity and encryption.
- **Proxies (Polipo, Privoxy, HAProxy):** Used to chain connections and filter traffic, adding layers of privacy.
- **WiFi Tools (Pixiewps, Wifipumpkin3):** Designed for security auditing, which, if used improperly, could have security implications. Proper usage and ethical guidelines are crucial.

### 8.3. Potential Vulnerabilities & Mitigations (Initial Thoughts)
- **External Tool Dependencies:** Reliance on external tools means vulnerabilities in those tools could impact AnonSuite. Mitigation involves keeping dependencies updated.
- **Configuration Errors:** Incorrect proxy configurations could lead to traffic leaks. Mitigation requires robust configuration validation and testing.
- **Shell Command Execution:** Executing external commands always carries a risk. Input sanitization and careful command construction are essential.
- **Privilege Escalation:** Some network operations might require elevated privileges. Least-privilege principles should be applied.

## 9. Testing Strategy (Current & Desired)

### 9.1. Current State
- `Makefile` includes a `test` target that runs `pytest`.
- The `/tests` directory is currently empty, indicating a lack of implemented tests.

### 9.2. Desired State (as per user requirement)
- **High-Level Functional Tests:** Tests should cover end-to-end scenarios, verifying the correct orchestration of Tor and proxies, and the effective functioning of WiFi auditing tools.
- **Complex Scenarios:** Tests should simulate various network conditions, proxy chain configurations, and potential error states.
- **Integration Tests:** Focus on the interaction between AnonSuite's Python code and the external tools it manages.
- **Unit Tests:** For core Python logic where applicable.

## 10. CI/CD Strategy (Desired)

### 10.1. GitHub Actions
- Implement GitHub Actions workflows for automated:
    - Linting (`ruff`)
    - Type-checking (`mypy`)
    - Testing (`pytest`)
    - Potentially building/packaging if applicable.

## 11. Future Considerations
- Enhanced error handling and user feedback for external tool failures.
- More robust dependency management and installation.
- Comprehensive documentation for users and developers.