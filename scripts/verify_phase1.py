#!/usr/bin/env python3
"""
AnonSuite Phase 1 Verification Script
Verifies that multitor component is working correctly
"""

import subprocess
import socket
import sys
import time
from pathlib import Path

def check_tor_process():
    """Check if Tor process is running"""
    try:
        result = subprocess.run(['pgrep', '-f', 'tor.*9000'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error checking Tor process: {e}")
        return False

def check_socks_port():
    """Check if SOCKS port 9000 is accessible"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', 9000))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Error checking SOCKS port: {e}")
        return False

def check_control_port():
    """Check if control port 9001 is accessible"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', 9001))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Error checking control port: {e}")
        return False

def check_tor_connectivity():
    """Test Tor connectivity via SOCKS proxy using curl"""
    try:
        result = subprocess.run([
            'curl', '--socks5-hostname', '127.0.0.1:9000', 
            'https://check.torproject.org/', '--silent', '--max-time', '30'
        ], capture_output=True, text=True, timeout=35)
        
        return result.returncode == 0 and 'Congratulations' in result.stdout
    except Exception as e:
        print(f"Error checking Tor connectivity: {e}")
        return False

def check_log_files():
    """Check if log files exist and are readable"""
    log_file = Path('/Users/morningstar/Desktop/AnonSuite/src/anonymity/multitor/multitor.log')
    tor_log = Path('/Users/morningstar/Desktop/AnonSuite/src/anonymity/multitor/tor_9000/tor.log')
    
    return log_file.exists() and tor_log.exists()

def main():
    """Run all verification checks"""
    print("🔍 AnonSuite Phase 1 Verification")
    print("=" * 40)
    
    checks = [
        ("Tor Process Running", check_tor_process),
        ("SOCKS Port (9000) Accessible", check_socks_port),
        ("Control Port (9001) Accessible", check_control_port),
        ("Log Files Present", check_log_files),
        ("Tor Connectivity Working", check_tor_connectivity),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"Checking {name}...", end=" ")
        try:
            result = check_func()
            status = "✅ PASS" if result else "❌ FAIL"
            print(status)
            results.append(result)
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append(False)
    
    print("\n" + "=" * 40)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 Phase 1 Complete! All {total} checks passed.")
        print("✅ Multitor component is fully operational")
        print("✅ Ready to proceed to Phase 2")
        return 0
    else:
        print(f"⚠️  Phase 1 Incomplete: {passed}/{total} checks passed")
        print("❌ Please resolve failing checks before proceeding")
        return 1

if __name__ == "__main__":
    sys.exit(main())
