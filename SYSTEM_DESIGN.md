# AnonSuite System Design

## 1. CLI Orchestrator

The primary user interface is `anonsuite.py`.

- **Functionality:**
  - On launch, it presents a main menu with two options: "Anonymity" and "Wi-Fi Auditing".
  - It uses simple, numbered menus and captures user input.
  - Based on user selection, it calls other scripts using Python's `subprocess` module.
  - It is responsible for requesting `sudo` privileges where necessary.

## 2. Anonymity Module

- **Activation:** Launched via the `anonsuite start` command (which is called by the Python orchestrator).
- **Process Flow:**
  1. The `anonsuite` Bash script is executed with `sudo`.
  2. It calls the `multitor` library to initialize a user-defined number of Tor processes, each on a different SOCKS port.
  3. `multitor` also starts an `haproxy` instance to load-balance traffic across the Tor processes.
  4. The `anonsuite` script then configures the system's `iptables` to redirect all TCP and UDP traffic (except for local traffic and Tor's own traffic) to the `haproxy` port.
  5. DNS requests are also redirected to be resolved over Tor to prevent DNS leaks.
- **Deactivation (`anonsuite stop`):**
  1. The `iptables` rules are flushed and restored from a backup.
  2. The `multitor --kill` command is called to terminate all `tor` and `haproxy` processes.

## 3. Wi-Fi Auditing Module

This module is a collection of two independent tools launched by the orchestrator.

- **Wifipumpkin3:**
  - **Launch:** The `run_wifipumpkin.sh` wrapper script is executed.
  - **Execution:** The script changes to the `wifipumpkin3` directory and executes its main Python script. `wifipumpkin3` then takes over the console and runs its own interactive session.
  - **Hardware:** Requires a wireless adapter capable of master mode.

- **Pixiewps:**
  - **Launch:** The `run_pixiewps.sh` wrapper script is executed.
  - **Execution:** The script changes to the `pixiewps` directory and executes the compiled `pixiewps` binary, passing along any command-line arguments provided by the user.
  - **Hardware:** Requires a wireless adapter capable of monitor mode.

## 4. Installation and Dependencies

- The `install.sh` script is the single source of truth for setup.
- **Dependencies:**
  - `tor`, `haproxy`, `privoxy`
  - `python3`, `pip`
  - `build-essential` (for compiling `pixiewps`)
  - Python packages listed in `wifipumpkin3/requirements.txt`.
- **Actions:**
  1. Creates `log` and `run` directories.
  2. Installs all `apt` dependencies.
  3. Installs all `pip` dependencies.
  4. Compiles the `pixiewps` binary.
  5. Creates symbolic links for `anonsuite` and `anonsurf` in `/usr/local/bin` for easy access.
