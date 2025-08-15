#!/usr/bin/env python3
"""
Network Performance Monitor for AnonSuite
Helps developers debug Tor circuit performance and network issues.

Author: Marcus (with some help from the team)
"""

import time
import subprocess
import json
import requests
import socket
from datetime import datetime
from typing import Dict, List, Optional
import argparse

class NetworkMonitor:
    """Monitor network performance for debugging AnonSuite issues"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = []
        
    def log(self, message: str) -> None:
        """Log message if verbose mode is on"""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {message}")
    
    def check_tor_connectivity(self) -> Dict:
        """Check if Tor is working and measure performance"""
        self.log("Checking Tor connectivity...")
        
        result = {
            "test": "tor_connectivity",
            "timestamp": datetime.now().isoformat(),
            "status": "unknown",
            "details": {}
        }
        
        try:
            # Test direct connection first
            start_time = time.time()
            direct_response = requests.get("http://httpbin.org/ip", timeout=10)
            direct_time = time.time() - start_time
            direct_ip = direct_response.json().get("origin", "unknown")
            
            result["details"]["direct_ip"] = direct_ip
            result["details"]["direct_time"] = round(direct_time, 2)
            
            # Test Tor connection (assuming SOCKS proxy on 9050)
            proxies = {
                'http': 'socks5://127.0.0.1:9050',
                'https': 'socks5://127.0.0.1:9050'
            }
            
            start_time = time.time()
            tor_response = requests.get("http://httpbin.org/ip", 
                                      proxies=proxies, timeout=15)
            tor_time = time.time() - start_time
            tor_ip = tor_response.json().get("origin", "unknown")
            
            result["details"]["tor_ip"] = tor_ip
            result["details"]["tor_time"] = round(tor_time, 2)
            result["details"]["slowdown_factor"] = round(tor_time / direct_time, 1)
            
            if direct_ip != tor_ip:
                result["status"] = "working"
                self.log(f"Tor is working! IP changed from {direct_ip} to {tor_ip}")
                self.log(f"Performance: Direct={direct_time:.2f}s, Tor={tor_time:.2f}s")
            else:
                result["status"] = "not_working"
                result["details"]["error"] = "IP address didn't change"
                
        except requests.exceptions.ProxyError:
            result["status"] = "proxy_error"
            result["details"]["error"] = "Can't connect to Tor proxy (is it running?)"
        except Exception as e:
            result["status"] = "error"
            result["details"]["error"] = str(e)
            
        return result
    
    def check_dns_leaks(self) -> Dict:
        """Check for DNS leaks that could compromise anonymity"""
        self.log("Checking for DNS leaks...")
        
        result = {
            "test": "dns_leaks",
            "timestamp": datetime.now().isoformat(),
            "status": "unknown",
            "details": {}
        }
        
        try:
            # Check what DNS servers we're actually using
            # This is a simplified check - real DNS leak testing is more complex
            dns_servers = []
            
            # Try to get DNS config (Linux/macOS)
            try:
                with open('/etc/resolv.conf', 'r') as f:
                    for line in f:
                        if line.startswith('nameserver'):
                            dns_servers.append(line.split()[1])
            except FileNotFoundError:
                # macOS alternative
                try:
                    dns_output = subprocess.check_output(['scutil', '--dns'], 
                                                       text=True, timeout=5)
                    # Parse DNS output (simplified)
                    for line in dns_output.split('\n'):
                        if 'nameserver[0]' in line:
                            dns_servers.append(line.split(':')[1].strip())
                except:
                    pass
            
            result["details"]["configured_dns"] = dns_servers
            
            # Check if we're using common public DNS (potential leak)
            public_dns = ['8.8.8.8', '8.8.4.4', '1.1.1.1', '1.0.0.1']
            leaky_dns = [dns for dns in dns_servers if dns in public_dns]
            
            if leaky_dns:
                result["status"] = "potential_leak"
                result["details"]["warning"] = f"Using public DNS: {leaky_dns}"
            else:
                result["status"] = "ok"
                
        except Exception as e:
            result["status"] = "error"
            result["details"]["error"] = str(e)
            
        return result
    
    def check_port_connectivity(self, ports: List[int] = None) -> Dict:
        """Check if required ports are accessible"""
        if ports is None:
            ports = [9050, 9051, 8118]  # Common Tor/proxy ports
            
        self.log(f"Checking port connectivity for {ports}...")
        
        result = {
            "test": "port_connectivity", 
            "timestamp": datetime.now().isoformat(),
            "details": {"ports": {}}
        }
        
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result_code = sock.connect_ex(('127.0.0.1', port))
                sock.close()
                
                if result_code == 0:
                    result["details"]["ports"][port] = "open"
                else:
                    result["details"]["ports"][port] = "closed"
                    
            except Exception as e:
                result["details"]["ports"][port] = f"error: {e}"
        
        open_ports = [p for p, status in result["details"]["ports"].items() 
                     if status == "open"]
        result["status"] = "ok" if len(open_ports) > 0 else "no_ports_open"
        
        return result
    
    def run_full_check(self) -> Dict:
        """Run all network checks and return comprehensive results"""
        self.log("Starting full network diagnostics...")
        
        full_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": []
        }
        
        # Run all checks
        checks = [
            self.check_port_connectivity,
            self.check_tor_connectivity,
            self.check_dns_leaks
        ]
        
        for check in checks:
            try:
                result = check()
                full_results["tests"].append(result)
                self.results.append(result)
            except Exception as e:
                error_result = {
                    "test": check.__name__,
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                full_results["tests"].append(error_result)
        
        # Overall assessment
        failed_tests = [t for t in full_results["tests"] 
                       if t["status"] in ["error", "not_working", "proxy_error"]]
        
        if len(failed_tests) == 0:
            full_results["overall_status"] = "healthy"
        elif len(failed_tests) < len(full_results["tests"]):
            full_results["overall_status"] = "partial_issues"
        else:
            full_results["overall_status"] = "major_issues"
            
        return full_results
    
    def save_results(self, filename: str = None) -> str:
        """Save results to file for later analysis"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"network_check_{timestamp}.json"
            
        filepath = f"/tmp/{filename}"
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
            
        return filepath

def main():
    parser = argparse.ArgumentParser(description="Network performance monitor for AnonSuite")
    parser.add_argument("-v", "--verbose", action="store_true", 
                       help="Verbose output")
    parser.add_argument("-s", "--save", action="store_true",
                       help="Save results to file")
    parser.add_argument("-p", "--ports", nargs="+", type=int,
                       help="Additional ports to check")
    
    args = parser.parse_args()
    
    monitor = NetworkMonitor(verbose=args.verbose)
    
    print("AnonSuite Network Monitor")
    print("=" * 40)
    
    results = monitor.run_full_check()
    
    # Print summary
    print(f"\nOverall Status: {results['overall_status'].upper()}")
    print(f"Tests Run: {len(results['tests'])}")
    
    for test in results["tests"]:
        status_symbol = "✓" if test["status"] in ["ok", "working"] else "✗"
        print(f"{status_symbol} {test['test']}: {test['status']}")
        
        # Show key details
        if test["test"] == "tor_connectivity" and "details" in test:
            details = test["details"]
            if "tor_time" in details and "direct_time" in details:
                print(f"  Performance: {details['slowdown_factor']}x slower than direct")
    
    if args.save:
        filepath = monitor.save_results()
        print(f"\nResults saved to: {filepath}")
    
    # Exit with error code if major issues
    if results["overall_status"] == "major_issues":
        exit(1)

if __name__ == "__main__":
    main()
