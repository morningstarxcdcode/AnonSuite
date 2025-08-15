# AnonSuite API Specification (CLI)

This document defines the command-line interface for the `AnonSuite` toolkit.

## 1. Main Entry Point: `anonsuite`

This is the primary command, which launches the interactive, menu-driven interface.

### Usage
```bash
sudo anonsuite
```

### Behavior
- Launches the `anonsuite.py` script.
- Presents the main menu:
  ```
  --- AnonSuite - Main Menu ---
    1. Anonymity
    2. Wi-Fi Auditing
    0. Back
  ```

## 2. Anonymity Module Interface

Accessed via option `1` from the main menu.

### Menu
```
--- Anonymity Module ---
  1. Start AnonSuite
  2. Stop AnonSuite
  3. Restart AnonSuite
  0. Back
```

### Commands
- **`Start AnonSuite`**: Executes `sudo /path/to/modules/anonymity/anonsuite start`. This initializes the multi-Tor proxy and redirects all system traffic through it.
- **`Stop AnonSuite`**: Executes `sudo /path/to/modules/anonymity/anonsuite stop`. This restores normal traffic flow and shuts down all Tor processes.
- **`Restart AnonSuite`**: Executes `stop` followed by `start`.

## 3. Wi-Fi Auditing Module Interface

Accessed via option `2` from the main menu.

### Menu
```
--- Wi-Fi Auditing Module ---
  1. Scan for Networks (not yet implemented)
  2. Rogue AP Attack (Wifipumpkin3)
  3. Pixie-Dust Attack (Pixiewps)
  0. Back
```

### Commands
- **`Rogue AP Attack (Wifipumpkin3)`**: Executes the `run_wifipumpkin.sh` wrapper script, which launches the interactive `wifipumpkin3` console.
- **`Pixie-Dust Attack (Pixiewps)`**: Prompts the user for command-line arguments and then executes the `run_pixiewps.sh` wrapper, passing the arguments to the `pixiewps` binary.
  - **Example Interaction:**
    ```
    Enter the arguments for Pixiewps: -e <pke> -s <hash1> -z <hash2> ...
    ```
