# AnonSuite Development Plan

This document outlines the plan for developing the AnonSuite toolkit.

## 1. Technology Stack

- **Orchestrator/Wrapper:** Python 3
- **Anonymity Module:** Bash (from `kali-anonsurf` and `multitor`)
- **Wi-Fi Module:** Python 3 (from `wifipumpkin3`), C (from `pixiewps`)
- **Installation:** Bash (`install.sh`)
- **Development Automation:** `Makefile`

## 2. Milestones

### M1: System Design & Scaffolding (Complete)
- **Deliverables:**
  - Create all required design and planning documents: `ARCHITECTURE.md`, `DEVELOPMENT_PLAN.md`, `SYSTEM_DESIGN.md`, `SECURITY_MODEL.md`, `API_SPEC.md`.
  - Create the repository structure with directories for modules, docs, scripts, etc.
  - Initialize `PROGRESS_LOG.md` and `NEXT_STEPS.md`.

### M2: Anonymity Module Integration
- **Deliverables:**
  - Copy `multitor` and `kali-anonsurf` source into the project.
  - Refactor the `kali-anonsurf` script to call `multitor` instead of a single `tor` service.
  - Ensure the module can successfully start and stop system-wide traffic redirection through multiple Tor instances.
  - Create a single `anonsuite` command to control this module.

### M3: Wi-Fi Module Integration
- **Deliverables:**
  - Copy `wifipumpkin3` and `pixiewps` source into the project.
  - Compile `pixiewps` into a binary.
  - Create simple wrapper scripts (`run_wifipumpkin.sh`, `run_pixiewps.sh`) to launch these tools with the correct paths and permissions.

### M4: Unified CLI
- **Deliverables:**
  - Develop the main `anonsuite.py` script.
  - Implement a menu-driven interface that allows the user to select and launch either the Anonymity or Wi-Fi Auditing modules.
  - Ensure the CLI can pass arguments correctly to the underlying tools (e.g., for `pixiewps`).

### M5: Finalization & Documentation
- **Deliverables:**
  - Create a comprehensive `install.sh` script that handles all dependencies and compilation.
  - Finalize the main `README.md` with a project overview, features, and a quickstart guide.
  - Create a `Makefile` with helper scripts for `install`, `clean`, and `run`.

## 3. Risk Analysis

- **Dependency Conflicts:** High. Addressed by a carefully ordered installation script.
- **Hardware Incompatibility:** High. Addressed by clear documentation of hardware requirements.
- **Root Permissions:** High. Addressed by clear security warnings in the documentation.
