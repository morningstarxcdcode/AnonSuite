#!/bin/bash

# AnonSuite Easy Installer
# This script helps users install AnonSuite and its dependencies
# Designed for accessibility and ease of use

set -e  # Exit on any error

echo "╔═══════════════════════════════════════╗"
echo "║       AnonSuite Easy Installer       ║"
echo "║     Making Security Tools Accessible ║"
echo "╚═══════════════════════════════════════╝"
echo ""

# Function to print colored output
print_status() {
    case $1 in
        "info") echo -e "\033[1;34m[INFO]\033[0m $2" ;;
        "success") echo -e "\033[1;32m[SUCCESS]\033[0m $2" ;;
        "warning") echo -e "\033[1;33m[WARNING]\033[0m $2" ;;
        "error") echo -e "\033[1;31m[ERROR]\033[0m $2" ;;
    esac
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to ask yes/no questions
ask_yes_no() {
    while true; do
        read -p "$1 (y/n): " yn
        case $yn in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo "Please answer yes or no.";;
        esac
    done
}

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command_exists apt; then
            OS="ubuntu"
        elif command_exists yum; then
            OS="centos"
        elif command_exists pacman; then
            OS="arch"
        else
            OS="linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    else
        OS="unknown"
    fi
}

# Install dependencies based on OS
install_dependencies() {
    print_status "info" "Installing dependencies for $OS..."
    
    case $OS in
        "ubuntu"|"debian")
            print_status "info" "Using apt package manager..."
            if ask_yes_no "Install tor, privoxy, and wireless tools?"; then
                sudo apt update
                sudo apt install -y tor privoxy wireless-tools aircrack-ng python3-pip
                print_status "success" "Dependencies installed successfully!"
            fi
            ;;
        "macos")
            if command_exists brew; then
                print_status "info" "Using Homebrew..."
                if ask_yes_no "Install tor and privoxy?"; then
                    brew install tor privoxy
                    print_status "success" "Dependencies installed successfully!"
                fi
            else
                print_status "warning" "Homebrew not found. Please install it first:"
                echo "Visit: https://brew.sh/"
                echo "Then run: brew install tor privoxy"
            fi
            ;;
        "arch")
            print_status "info" "Using pacman..."
            if ask_yes_no "Install tor, privoxy, and wireless tools?"; then
                sudo pacman -S tor privoxy wireless_tools aircrack-ng python-pip
                print_status "success" "Dependencies installed successfully!"
            fi
            ;;
        *)
            print_status "warning" "Automatic installation not supported for your OS."
            print_status "info" "Please install manually:"
            echo "  - Tor: https://www.torproject.org/download/"
            echo "  - Privoxy: http://www.privoxy.org/"
            echo "  - Wireless tools (Linux only)"
            ;;
    esac
}

# Check Python installation
check_python() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
        print_status "success" "Python $PYTHON_VERSION found"
        
        # Check if version is sufficient (3.6+)
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 6) else 1)"; then
            print_status "success" "Python version is sufficient"
        else
            print_status "warning" "Python 3.6+ recommended"
        fi
    else
        print_status "error" "Python 3 not found. Please install Python 3.6 or later."
        exit 1
    fi
}

# Run configuration wizard
setup_config() {
    print_status "info" "Setting up AnonSuite configuration..."
    
    if ask_yes_no "Run the configuration wizard?"; then
        echo ""
        print_status "info" "Starting configuration wizard..."
        echo "You can accept defaults by pressing Enter"
        echo ""
        
        # Provide default answers for common settings
        echo -e "INFO\nrun\n" | python3 -m src.anonsuite --config-wizard
        
        if [ $? -eq 0 ]; then
            print_status "success" "Configuration completed!"
        else
            print_status "warning" "Configuration had issues, but you can try again later"
        fi
    fi
}

# Run health check
run_health_check() {
    print_status "info" "Running system health check..."
    echo ""
    
    python3 -m src.anonsuite --health-check
    
    echo ""
    print_status "info" "Health check complete. Don't worry if some items failed - you can still use AnonSuite!"
}

# Show next steps
show_next_steps() {
    echo ""
    print_status "success" "Installation complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Try demo mode: python3 -m src.anonsuite --demo"
    echo "  2. Learn concepts: python3 -m src.anonsuite --explain tor"
    echo "  3. Run health check: python3 -m src.anonsuite --health-check"
    echo "  4. Start using: python3 -m src.anonsuite"
    echo ""
    echo "For help and documentation:"
    echo "  - Read ACCESSIBILITY_GUIDE.md for detailed help"
    echo "  - Check docs/ folder for more information"
    echo "  - Visit: https://github.com/morningstarxcdcode/AnonSuite"
    echo ""
    print_status "info" "Remember: Only use on networks you own or have permission to test!"
}

# Main installation flow
main() {
    # Check if we're in the right directory
    if [ ! -f "src/anonsuite/main.py" ]; then
        print_status "error" "Please run this script from the AnonSuite root directory"
        exit 1
    fi
    
    print_status "info" "Welcome to the AnonSuite Easy Installer!"
    echo "This script will help you set up AnonSuite with minimal effort."
    echo ""
    
    # Check Python
    check_python
    
    # Detect OS and show info
    detect_os
    print_status "info" "Detected OS: $OS"
    echo ""
    
    # Install dependencies
    if ask_yes_no "Install system dependencies?"; then
        install_dependencies
        echo ""
    else
        print_status "info" "Skipping dependency installation"
        print_status "info" "You can install manually or run demo mode without dependencies"
        echo ""
    fi
    
    # Setup configuration
    setup_config
    echo ""
    
    # Run health check
    if ask_yes_no "Run health check to see what's working?"; then
        run_health_check
    fi
    
    # Show next steps
    show_next_steps
}

# Run main function
main "$@"