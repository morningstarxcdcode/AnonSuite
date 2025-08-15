# Technical Architecture: AnonSuite

## 1. Architectural Principles

As Marcus, a seasoned architect, my approach to AnonSuite's technical architecture is rooted in pragmatism, maintainability, and security. We're building a tool that needs to be reliable in sensitive contexts, so clarity, robustness, and a clear separation of concerns are paramount. We'll favor established, battle-tested technologies and patterns over trendy, unproven ones.

-   **Modularity:** Components should be loosely coupled, allowing for independent development, testing, and replacement.
-   **Reliability:** Robust error handling, logging, and graceful degradation are critical, especially when dealing with network operations and external tools.
-   **Security-First:** Every design decision will consider potential security implications, from process isolation to data handling.
-   **Portability:** While initially focused on macOS/Linux, the architecture should avoid platform-specific dependencies where possible, or clearly abstract them.
-   **Observability:** Comprehensive logging and status reporting are essential for debugging and understanding runtime behavior.
-   **Human-Readability:** Code and configuration should be clear, well-structured, and commented to explain *why*, not just *what*.

## 2. Core Components & Technology Stack

AnonSuite is fundamentally a CLI orchestration tool. Its core strength lies in effectively managing and chaining existing, specialized binaries.

### 2.1. Primary Language & Execution Environment

-   **Bash (Shell Scripting):** The `multitor` component, which is the heart of the anonymity features, is implemented in Bash. This choice is pragmatic for direct process control, `sudo` integration, and seamless execution of external binaries (Tor, Privoxy, HAProxy). It allows for low-level system interaction and avoids Python overhead for critical network plumbing.
-   **Python:** The main `anonsuite.py` CLI will be implemented in Python. This provides a higher-level, more user-friendly interface for argument parsing, command dispatching, and potentially more complex logic (e.g., data processing for WiFi tools, user configuration management). Python's rich ecosystem and readability make it ideal for the user-facing layer.

### 2.2. Anonymity & Proxy Chain Components

-   **Tor:** The Onion Router, providing the foundational anonymity layer. We'll manage multiple Tor instances, each with its own SOCKS and Control ports.
-   **Privoxy:** A non-caching web proxy, used for filtering web content and forwarding requests through a parent SOCKS proxy (Tor or HAProxy).
-   **HAProxy:** A high-performance TCP/HTTP load balancer. In our context, it acts as a frontend for multiple Tor SOCKS proxies, distributing traffic and providing a single entry point for other proxies (like Privoxy) or applications.
-   **Data Directories:** Each Tor instance requires a dedicated, user-owned data directory for its state and logs.

### 2.3. WiFi Auditing Components

-   **Pixiewps:** A tool for offline brute-forcing of WPS PINs.
-   **Wifipumpkin3:** A comprehensive framework for rogue access point attacks, deauthentication, and credential harvesting.
-   **Integration Strategy:** These will be executed as external processes, with `anonsuite.py` acting as the orchestrator, passing arguments and parsing output.

### 2.4. Configuration Management

-   **Bash Templates (`etc/templates/`):** Configuration files for Privoxy and HAProxy are managed as templates. These templates are dynamically populated with generated ports, passwords, and backend server lists before the respective proxy services are launched.
-   **Environment Variables (`.env.example`):** For sensitive data or user-specific settings that shouldn't be hardcoded.

### 2.5. Logging & Observability

-   **Centralized Logging:** All critical operations and errors from `multitor` and its helper scripts are logged to a single `multitor.log` file with timestamps and context. This is crucial for debugging and understanding the flow of operations.
-   **Live Output:** Key messages are also `tee`d to `stdout` for real-time user feedback.

## 3. System Flow & Interactions

### 3.1. Main CLI (`anonsuite.py`)

-   Parses user commands and arguments.
-   Dispatches calls to underlying Bash scripts (e.g., `multitor`) or Python modules.
-   Provides user-friendly output and error messages.

### 3.2. Multitor Orchestration (Bash)

-   **Binary Validation:** Performs pre-flight checks to ensure all required external binaries (Tor, Privoxy, HAProxy, pidof) exist and are executable using their absolute paths.
-   **Process Management:** Responsible for launching, monitoring, and gracefully terminating Tor and proxy processes.
-   **Dynamic Configuration:** Generates runtime configuration files for proxies based on user input and available Tor SOCKS ports.
-   **Error Handling:** Captures and logs errors from external binary executions.

### 3.3. Inter-Component Communication

-   **Shell Execution:** The primary mode of communication between `anonsuite.py` and `multitor` (and its helpers) is via shell command execution.
-   **File-based Communication:** Configuration files and log files serve as a means of passing state and information between components.

## 4. Data Model (Minimal)

For the core `multitor` component, the data model is minimal, primarily consisting of:

-   **Tor Data Directories:** Local directories for each Tor instance, containing its state, keys, and logs.
-   **Proxy Configuration Files:** Dynamically generated `.cfg` files for Privoxy and HAProxy.
-   **Log Files:** Text-based logs for operational insights.

For future Python-based features (e.g., user profiles, persistent settings for WiFi tools), a lightweight database like **SQLite** might be introduced to manage structured data locally.

## 5. Security Model & Mitigations

Security is paramount for an anonymity tool. Our model focuses on:

-   **Least Privilege:** Tor and proxy processes will run under dedicated, unprivileged users where possible (e.g., `debian-tor` or the user's own account if configured correctly).
-   **Process Isolation:** Each Tor instance operates with its own data directory, minimizing cross-contamination.
-   **Secure Configuration:** Templates are used to prevent accidental exposure of sensitive data. Passwords for control ports are generated dynamically.
-   **Input Validation:** While Bash scripts have limited built-in validation, the Python CLI will perform robust input sanitization.
-   **Absolute Paths:** Hardcoding absolute paths for binaries mitigates `PATH` injection vulnerabilities.
-   **Data Directory Ownership:** Ensuring Tor data directories are owned by the correct user prevents unauthorized access and data corruption.

## 6. Testing Strategy

Our testing strategy will be comprehensive, focusing on reliability and correctness:

-   **Unit Tests (Python):** For `anonsuite.py`'s internal logic.
-   **Integration Tests (Bash/Python):** Crucial for `multitor`. These will verify the correct startup, chaining, and termination of Tor and proxy processes, and confirm network connectivity through the chain.
-   **Functional/End-to-End Tests:** Simulate user scenarios through the `anonsuite.py` CLI, verifying the overall system behavior.
-   **Performance Tests:** For critical paths (e.g., proxy chain setup time).

## 7. Deployment & Environment

AnonSuite is designed for local deployment. Installation will involve:

-   Cloning the repository.
-   Installing external dependencies (Tor, Privoxy, HAProxy) via package managers (e.g., Homebrew on macOS).
-   Running an `install.sh` script (or similar) to set up permissions and initial configurations.

## 8. Observability & Debugging

-   **Detailed Logging:** The `multitor.log` file will be the primary source for debugging runtime issues.
-   **Live Output:** `tee`ing logs to `stdout` provides immediate feedback during execution.
-   **Error Reporting:** Clear error messages in logs and terminal output will guide troubleshooting.

## 9. Future Architectural Considerations

-   **Cross-Platform Abstraction:** Investigate more platform-agnostic ways to manage processes and permissions (e.g., using Python's `subprocess` more extensively with careful privilege handling).
-   **Dynamic Port Management:** Implement logic to automatically find and assign available ports for Tor and proxies to avoid conflicts.
-   **Configuration Layer:** A more sophisticated configuration system (e.g., YAML/JSON with schema validation) for complex setups.
-   **Modular Proxy Integration:** A more pluggable system for adding new proxy types without modifying core `multitor` logic.

This architecture provides a solid foundation for AnonSuite, balancing direct system control with maintainability and future extensibility.
