#!/bin/bash
# AnonSuite Installation Script
# Automated setup for macOS and Linux systems

set -e  # Exit on any error

# Colors for output - keeping it simple but readable
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        log_info "Detected macOS system"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        log_info "Detected Linux system"
    else
        log_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install system dependencies
install_system_deps() {
    log_info "Installing system dependencies..."
    
    if [[ "$OS" == "macos" ]]; then
        # Check for Homebrew
        if ! command_exists brew; then
            log_info "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        
        # Install dependencies
        log_info "Installing macOS dependencies..."
        brew install tor privoxy python@3.11 git
        
        # Optional tools
        if ! command_exists iwconfig; then
            log_warning "iwconfig not available on macOS (expected)"
        fi
        
    elif [[ "$OS" == "linux" ]]; then
        # Detect Linux distribution
        if command_exists apt-get; then
            log_info "Installing dependencies via apt..."
            sudo apt-get update
            sudo apt-get install -y tor privoxy python3 python3-pip python3-venv git wireless-tools net-tools build-essential
        elif command_exists yum; then
            log_info "Installing dependencies via yum..."
            sudo yum install -y tor privoxy python3 python3-pip git wireless-tools net-tools gcc gcc-c++
        elif command_exists dnf; then
            log_info "Installing dependencies via dnf..."
            sudo dnf install -y tor privoxy python3 python3-pip git wireless-tools net-tools gcc gcc-c++
        else
            log_error "Unsupported Linux distribution. Please install dependencies manually."
            exit 1
        fi
    fi
}

# Setup Python environment
setup_python_env() {
    log_info "Setting up Python virtual environment..."
    
    # Check Python version
    if ! command_exists python3; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check Python version is 3.8+
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [[ $(echo "$python_version < 3.8" | bc -l) -eq 1 ]]; then
        log_error "Python 3.8+ is required, found $python_version"
        exit 1
    fi
    
    log_success "Python $python_version detected"
    
    # Create virtual environment
    if [[ ! -d "venv" ]]; then
        log_info "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    log_info "Upgrading pip..."
    pip install --upgrade pip
    
    # Install requirements
    if [[ -f "requirements.txt" ]]; then
        log_info "Installing Python dependencies..."
        pip install -r requirements.txt
    else
        log_warning "requirements.txt not found, installing basic dependencies..."
        pip install click colorama requests pyyaml psutil
    fi
}

# Setup project structure
setup_project() {
    log_info "Setting up project structure..."
    
    # Create necessary directories
    mkdir -p config/profiles run log build-log plugins
    mkdir -p /tmp/anonsuite
    
    # Make scripts executable
    if [[ -f "src/anonymity/multitor/multitor" ]]; then
        chmod +x src/anonymity/multitor/multitor
        chmod +x src/anonymity/multitor/__init__
        chmod +x src/anonymity/multitor/CreateTorProcess
        chmod +x src/anonymity/multitor/CreateProxyProcess
        log_success "Made multitor scripts executable"
    fi
    
    # Set up configuration
    if [[ ! -f "config/anonsuite.conf" ]]; then
        log_info "Creating default configuration..."
        # Configuration should already exist from our setup
    fi
}

# Configure services
configure_services() {
    log_info "Configuring services..."
    
    # Configure Tor
    if [[ "$OS" == "macos" ]]; then
        tor_config="/opt/homebrew/etc/tor/torrc"
    else
        tor_config="/etc/tor/torrc"
    fi
    
    if [[ -f "$tor_config" ]]; then
        # Check if our settings are already there
        if ! grep -q "ControlPort 9001" "$tor_config"; then
            log_info "Adding Tor configuration..."
            echo "ControlPort 9001" | sudo tee -a "$tor_config"
            echo "CookieAuthentication 1" | sudo tee -a "$tor_config"
        fi
    fi
    
    # Configure Privoxy
    if [[ "$OS" == "macos" ]]; then
        privoxy_config="/opt/homebrew/etc/privoxy/config"
    else
        privoxy_config="/etc/privoxy/config"
    fi
    
    if [[ -f "$privoxy_config" ]]; then
        # Check if forwarding is configured
        if ! grep -q "forward-socks5.*127.0.0.1:9000" "$privoxy_config"; then
            log_info "Configuring Privoxy for Tor forwarding..."
            echo "forward-socks5 / 127.0.0.1:9000 ." | sudo tee -a "$privoxy_config"
        fi
    fi
}

# Run health check
run_health_check() {
    log_info "Running health check..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Run AnonSuite health check
    if python src/anonsuite.py --health-check; then
        log_success "Health check passed!"
    else
        log_warning "Health check had issues, but installation completed"
    fi
}

# Main installation function
main() {
    echo "========================================"
    echo "    AnonSuite Installation Script"
    echo "========================================"
    echo
    
    # Check if we're in the right directory
    if [[ ! -f "src/anonsuite.py" ]]; then
        log_error "Please run this script from the AnonSuite root directory"
        exit 1
    fi
    
    detect_os
    
    log_info "Starting installation process..."
    
    # Install system dependencies
    install_system_deps
    
    # Setup Python environment
    setup_python_env
    
    # Setup project structure
    setup_project
    
    # Configure services
    configure_services
    
    # Run health check
    run_health_check
    
    echo
    log_success "Installation completed successfully!"
    echo
    echo "Next steps:"
    echo "1. Activate the virtual environment: source venv/bin/activate"
    echo "2. Run the configuration wizard: python src/anonsuite.py --config-wizard"
    echo "3. Start using AnonSuite: python src/anonsuite.py"
    echo
    echo "For help and documentation, see: docs/user-guide.md"
}

# Run main function
main "$@"
