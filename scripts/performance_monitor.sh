#!/bin/bash
# Performance Monitor for AnonSuite
# Tracks system performance during security operations
# Author: Marcus (because I got tired of manually checking htop)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/tmp/anonsuite_performance.log"
MONITOR_INTERVAL=5  # seconds

# Colors for output (because life's too short for boring logs)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_message() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARNING:${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1" >> "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ERROR:${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >> "$LOG_FILE"
}

check_system_resources() {
    # CPU usage
    cpu_usage=$(top -l 1 -s 0 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
    
    # Memory usage (macOS specific - would need adjustment for Linux)
    memory_info=$(vm_stat | grep -E "(free|active|inactive|wired)")
    
    # Disk usage for temp directory
    disk_usage=$(df -h /tmp | tail -1 | awk '{print $5}' | sed 's/%//')
    
    log_message "CPU: ${cpu_usage}%, Disk (/tmp): ${disk_usage}%"
    
    # Warn if resources are getting tight
    if (( $(echo "$cpu_usage > 80" | bc -l) )); then
        log_warning "High CPU usage: ${cpu_usage}%"
    fi
    
    if (( disk_usage > 90 )); then
        log_warning "High disk usage in /tmp: ${disk_usage}%"
    fi
}

check_tor_processes() {
    tor_count=$(pgrep -c tor || echo "0")
    anonsuite_count=$(pgrep -cf anonsuite || echo "0")
    
    log_message "Processes: Tor=$tor_count, AnonSuite=$anonsuite_count"
    
    if [ "$tor_count" -eq 0 ]; then
        log_warning "No Tor processes detected"
    fi
}

check_network_connections() {
    # Check for connections on common Tor ports
    tor_ports=(9050 9051 8118)
    active_ports=()
    
    for port in "${tor_ports[@]}"; do
        if lsof -i :$port >/dev/null 2>&1; then
            active_ports+=($port)
        fi
    done
    
    if [ ${#active_ports[@]} -gt 0 ]; then
        log_message "Active Tor ports: ${active_ports[*]}"
    else
        log_warning "No Tor ports active"
    fi
}

check_temp_files() {
    # Check for AnonSuite temp files
    temp_files=$(find /tmp -name "*anonsuite*" -o -name "*tor*" 2>/dev/null | wc -l)
    temp_size=$(du -sh /tmp/anonsuite* /tmp/tor* 2>/dev/null | awk '{sum+=$1} END {print sum}' || echo "0")
    
    log_message "Temp files: $temp_files files"
    
    if [ "$temp_files" -gt 100 ]; then
        log_warning "Many temp files detected: $temp_files"
    fi
}

performance_snapshot() {
    log_message "=== Performance Snapshot ==="
    check_system_resources
    check_tor_processes
    check_network_connections
    check_temp_files
    log_message "=========================="
}

continuous_monitor() {
    log_message "Starting continuous performance monitoring (interval: ${MONITOR_INTERVAL}s)"
    log_message "Press Ctrl+C to stop"
    
    trap 'log_message "Monitoring stopped"; exit 0' INT
    
    while true; do
        performance_snapshot
        sleep $MONITOR_INTERVAL
    done
}

show_summary() {
    if [ ! -f "$LOG_FILE" ]; then
        echo "No performance log found at $LOG_FILE"
        return
    fi
    
    echo "Performance Summary:"
    echo "==================="
    
    # Count warnings and errors
    warnings=$(grep -c "WARNING" "$LOG_FILE" || echo "0")
    errors=$(grep -c "ERROR" "$LOG_FILE" || echo "0")
    
    echo "Warnings: $warnings"
    echo "Errors: $errors"
    
    # Show recent entries
    echo ""
    echo "Recent entries:"
    tail -10 "$LOG_FILE"
}

cleanup_logs() {
    if [ -f "$LOG_FILE" ]; then
        rm "$LOG_FILE"
        echo "Performance log cleaned up"
    else
        echo "No log file to clean"
    fi
}

show_help() {
    echo "AnonSuite Performance Monitor"
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  snapshot    Take a single performance snapshot"
    echo "  monitor     Start continuous monitoring"
    echo "  summary     Show performance summary"
    echo "  cleanup     Clean up log files"
    echo "  help        Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 snapshot              # Quick system check"
    echo "  $0 monitor               # Continuous monitoring"
    echo "  $0 summary               # View recent performance data"
}

# Main script logic
case "${1:-snapshot}" in
    "snapshot")
        performance_snapshot
        ;;
    "monitor")
        continuous_monitor
        ;;
    "summary")
        show_summary
        ;;
    "cleanup")
        cleanup_logs
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
