# Makefile for AnonSuite

.PHONY: all install clean run help

# Define project structure
SRC_DIR = src
SCRIPTS_DIR = scripts

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  install   - Run the installation script to set up dependencies."
	@echo "  run       - Run the main AnonSuite application."
	@echo "  clean     - Remove temporary files and compiled binaries."

install:
	@echo "Running installation script..."
	@sudo bash $(SCRIPTS_DIR)/install.sh

run:
	@echo "Launching AnonSuite..."
	@sudo python3 $(SRC_DIR)/anonsuite.py

clean:
	@echo "Cleaning project..."
	@rm -f $(SRC_DIR)/wifi/pixiewps/pixiewps
	@find . -type d -name "__pycache__" -exec rm -r {} +
	@echo "Done."