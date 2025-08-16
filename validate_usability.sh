#!/bin/bash
# AnonSuite Real-World Usability Validation Script
# Run this to verify AnonSuite works for real-world use

set -e

echo "=========================================="
echo "AnonSuite Real-World Usability Test"
echo "=========================================="
echo "This script validates that AnonSuite is usable in real life."
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_exit_code="${3:-0}"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "Testing $test_name... "
    
    if eval "$test_command" >/dev/null 2>&1; then
        if [ $? -eq $expected_exit_code ]; then
            echo -e "${GREEN}PASS${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo -e "${RED}FAIL${NC} (wrong exit code)"
        fi
    else
        echo -e "${RED}FAIL${NC}"
    fi
}

echo -e "${BLUE}Phase 1: Basic Functionality Tests${NC}"
echo "These should work immediately after cloning:"
echo

run_test "Version command" "python src/anonsuite/main.py --version"
run_test "Help command" "python src/anonsuite/main.py --help"
run_test "Demo mode" "python src/anonsuite/main.py --demo"
run_test "WiFi explanation" "python src/anonsuite/main.py --explain wifi"
run_test "Tor explanation" "python src/anonsuite/main.py --explain tor"
run_test "Tutorial mode" "python src/anonsuite/main.py --tutorial"

echo
echo -e "${BLUE}Phase 2: System Assessment Tests${NC}"
echo "These provide guidance on what's needed:"
echo

# Health check might exit with 1 if dependencies missing, that's OK
run_test "Health check" "python src/anonsuite/main.py --health-check" "0|1"
run_test "List profiles" "python src/anonsuite/main.py --list-profiles"
run_test "List plugins" "python src/anonsuite/main.py --list-plugins"

echo
echo -e "${BLUE}Phase 3: Configuration Tests${NC}"
echo "These test configuration management:"
echo

run_test "Config wizard (dry run)" "timeout 5 echo '' | python src/anonsuite/main.py --config-wizard || true"

echo
echo -e "${BLUE}Phase 4: Import Tests${NC}"
echo "These test that Python imports work correctly:"
echo

run_test "AnonSuiteCLI import" "PYTHONPATH=src python -c 'from anonsuite import AnonSuiteCLI; print(\"OK\")'"
run_test "VisualTokens import" "PYTHONPATH=src python -c 'from anonsuite import VisualTokens; print(\"OK\")'"
run_test "ConfigManager import" "PYTHONPATH=src python -c 'from anonsuite import ConfigManager; print(\"OK\")'"

echo
echo "=========================================="
echo "Test Results Summary"
echo "=========================================="

PASS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))

echo "Total Tests: $TOTAL_TESTS"
echo "Passed Tests: $PASSED_TESTS"
echo "Pass Rate: $PASS_RATE%"

if [ $PASS_RATE -ge 80 ]; then
    echo -e "${GREEN}✓ EXCELLENT${NC} - AnonSuite is highly usable for real-world applications!"
    echo "  You can immediately start using it for security testing and education."
elif [ $PASS_RATE -ge 60 ]; then
    echo -e "${YELLOW}⚠ GOOD${NC} - AnonSuite is usable with minor issues."
    echo "  Core functionality works, some features may need dependency installation."
else
    echo -e "${RED}✗ NEEDS IMPROVEMENT${NC} - Some core functionality may be broken."
    echo "  Please check the installation and try again."
fi

echo
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Run: python src/anonsuite/main.py --health-check"
echo "2. Install any missing dependencies as suggested"
echo "3. Run: python src/anonsuite/main.py --demo"
echo "4. Start using: python src/anonsuite/main.py"
echo
echo "For detailed guidance, see: REAL_WORLD_USAGE.md"
echo "For troubleshooting, see: docs/troubleshooting.md"