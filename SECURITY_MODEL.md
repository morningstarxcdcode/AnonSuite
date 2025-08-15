# AnonSuite Security Model

## 1. Core Security Principle: Assumed Trust

This tool is designed for security professionals and researchers to use on **systems they control** and for **authorized security audits**. It is **not** designed to be a secure application in a multi-user or untrusted environment.

## 2. Privilege Requirements

- **Root Access (`sudo`):** `AnonSuite` requires root privileges for its core functionality.
  - **Anonymity Module:** Modifying system `iptables` requires root. Binding to privileged ports also requires root.
  - **Wi-Fi Module:** Putting a wireless card into monitor mode or master mode requires root.
- **Implication:** Any user who can run `AnonSuite` effectively has root access to the machine. The tool should only be available to trusted administrative users.

## 3. Network Security

- **Anonymity:** The purpose of the anonymity module is to enhance the user's network privacy by routing traffic through Tor. However, the Tor network itself has its own risks (e.g., malicious exit nodes).
- **Wi-Fi Attacks:** The Wi-Fi module is designed to perform active network attacks. These actions are inherently "insecure" from the perspective of the target network and should only be performed with explicit, written authorization.

## 4. Secrets and Configuration

- The `AnonSuite` toolkit does not manage any long-lived secrets, API keys, or passwords.
- The Tor control password is generated randomly on each run and is not persisted.
- There is no `.env` file required for secrets, as none exist.

## 5. Summary of Risks

- **Execution Risk:** A malicious actor with access to run `AnonSuite` can gain full control over the host system.
- **Network Risk:** The tool can be used to disrupt or monitor networks. Misuse can have serious consequences.
- **Conclusion:** `AnonSuite` is a powerful weapon for a security professional's arsenal. Like any weapon, it should be handled with extreme care and only used ethically and legally.
