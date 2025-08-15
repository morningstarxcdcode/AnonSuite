# AnonSuite Manual Test Plan

## 1. Introduction

This document provides a manual testing plan for the `AnonSuite` toolkit. Due to the nature of the application, which involves system-wide network changes and hardware interaction, automated testing is not feasible. These tests must be performed manually on a compatible, Debian-based Linux system with the appropriate hardware.

**Prerequisites:**
- A compatible Linux environment (e.g., Kali Linux).
- `sudo` privileges.
- A Wi-Fi adapter capable of monitor and master mode.

## 2. Test Cases

### Test Case 1: Installation

1.  **Description:** Ensure the `install` command in the `Makefile` runs without errors.
2.  **Steps:**
    1.  Open a terminal in the `AnonSuite` project root.
    2.  Run `make install`.
    3.  Enter the `sudo` password when prompted.
3.  **Expected Result:** The script completes with the message "AnonSuite installed successfully." All dependencies should be installed, `pixiewps` should be compiled, and symbolic links should be created in `/usr/local/bin`.

### Test Case 2: Anonymity Module - Start & Verify

1.  **Description:** Ensure the anonymity module can start and successfully route system traffic through the Tor network.
2.  **Steps:**
    1.  Run `make run` (or `sudo anonsuite`).
    2.  From the main menu, select `1` for "Anonymity".
    3.  From the anonymity menu, select `1` for "Start AnonSuite".
    4.  Wait for the process to complete.
    5.  Open a new terminal and run `curl https://api.ipify.org`. Note the IP address.
    6.  Run `ps aux | grep tor` and `ps aux | grep haproxy` to verify the processes are running.
3.  **Expected Result:** The IP address returned by `curl` should be a Tor exit node, not your real public IP. The `ps` commands should show multiple `tor` processes and one `haproxy` process.

### Test Case 3: Anonymity Module - Stop & Verify

1.  **Description:** Ensure the anonymity module can stop and restore normal internet traffic.
2.  **Steps:**
    1.  With the anonymity module running, select `2` for "Stop AnonSuite" from the anonymity menu.
    2.  Wait for the process to complete.
    3.  In another terminal, run `curl https://api.ipify.org` again.
    4.  Run `ps aux | grep tor` and `ps aux | grep haproxy`.
3.  **Expected Result:** The IP address returned should be your real public IP. The `ps` commands should show no running `tor` or `haproxy` processes related to `AnonSuite`.

### Test Case 4: Wi-Fi Module - Launch Wifipumpkin3

1.  **Description:** Ensure the `wifipumpkin3` tool can be launched from the menu.
2.  **Steps:**
    1.  Run `make run`.
    2.  From the main menu, select `2` for "Wi-Fi Auditing".
    3.  From the Wi-Fi menu, select `2` for "Rogue AP Attack (Wifipumpkin3)".
3.  **Expected Result:** The `wifipumpkin3` interactive console should launch and take over the current terminal session.

### Test Case 5: Wi-Fi Module - Launch Pixiewps

1.  **Description:** Ensure the `pixiewps` tool can be launched with arguments from the menu.
2.  **Steps:**
    1.  Run `make run`.
    2.  From the main menu, select `2` for "Wi-Fi Auditing".
    3.  From the Wi-Fi menu, select `3` for "Pixie-Dust Attack (Pixiewps)".
    4.  When prompted, enter `--help` as the arguments.
3.  **Expected Result:** The `pixiewps` help menu should be displayed in the terminal, demonstrating that the tool was executed correctly with the provided arguments.
