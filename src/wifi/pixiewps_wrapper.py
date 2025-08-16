#!/usr/bin/env python3
"""
Pixiewps Wrapper - WPS PIN Recovery Interface
Part of AnonSuite WiFi Auditing Tools
"""

import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class PixiewpsWrapper:
    """Wrapper for pixiewps WPS PIN recovery tool"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.pixiewps_path = "/Users/morningstar/Desktop/AnonSuite/src/wifi/pixiewps/pixiewps"
        self.results_dir = "/Users/morningstar/Desktop/AnonSuite/run/pixiewps_results"
        self._ensure_results_dir()

    def _ensure_results_dir(self):
        """Ensure results directory exists"""
        os.makedirs(self.results_dir, exist_ok=True)

    def check_binary(self) -> bool:
        """Check if pixiewps binary exists and is executable"""
        if not Path(self.pixiewps_path).is_file():
            self.logger.error(f"Pixiewps binary not found at {self.pixiewps_path}")
            return False

        if not os.access(self.pixiewps_path, os.X_OK):
            self.logger.error(f"Pixiewps binary is not executable: {self.pixiewps_path}")
            return False

        return True

    def run_attack(self, pke: str, pkr: str, e_hash1: str, e_hash2: str,
                   authkey: str, e_nonce: str, r_nonce: Optional[str] = None,
                   e_bssid: Optional[str] = None, verbosity: int = 3,
                   output_file: Optional[str] = None) -> Dict:
        """
        Run pixiewps attack with provided WPS handshake data

        Args:
            pke: Enrollee public key
            pkr: Registrar public key
            e_hash1: Enrollee hash-1
            e_hash2: Enrollee hash-2
            authkey: Authentication session key
            e_nonce: Enrollee nonce
            r_nonce: Registrar nonce (optional)
            e_bssid: Enrollee BSSID (optional)
            verbosity: Verbosity level 1-3
            output_file: Output file path (optional)

        Returns:
            Dict with attack results
        """
        if not self.check_binary():
            return {"status": "error", "message": "Pixiewps binary not available"}

        # Build command
        command = [
            self.pixiewps_path,
            "-e", pke,
            "-r", pkr,
            "-s", e_hash1,
            "-z", e_hash2,
            "-a", authkey,
            "-n", e_nonce,
            "-v", str(verbosity)
        ]

        # Add optional parameters
        if r_nonce:
            command.extend(["-m", r_nonce])
        if e_bssid:
            command.extend(["-b", e_bssid])
        if output_file:
            command.extend(["-o", output_file])

        try:
            self.logger.info("Running pixiewps attack...")
            self.logger.debug(f"Command: {' '.join(command)}")

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            # Parse results
            attack_result = self._parse_results(result, command)

            # Save results
            self._save_results(attack_result)

            return attack_result

        except subprocess.TimeoutExpired:
            self.logger.error("Pixiewps attack timed out")
            return {"status": "error", "message": "Attack timed out"}
        except Exception as e:
            self.logger.error(f"Error running pixiewps: {e}")
            return {"status": "error", "message": str(e)}

    def _parse_results(self, result: subprocess.CompletedProcess, command: List[str]) -> Dict:
        """Parse pixiewps output and return structured results"""
        attack_result = {
            "status": "success" if result.returncode == 0 else "failed",
            "timestamp": datetime.now().isoformat(),
            "command": " ".join(command),
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "wps_pin": None,
            "psk": None,
            "ssid": None
        }

        # Parse successful output for WPS PIN and PSK
        if result.returncode == 0 and result.stdout:
            lines = result.stdout.split('\n')
            for line in lines:
                line = line.strip()
                if "WPS PIN:" in line:
                    attack_result["wps_pin"] = line.split("WPS PIN:")[-1].strip()
                elif "WPA PSK:" in line:
                    attack_result["psk"] = line.split("WPA PSK:")[-1].strip()
                elif "SSID:" in line:
                    attack_result["ssid"] = line.split("SSID:")[-1].strip()

        return attack_result

    def _save_results(self, results: Dict):
        """Save attack results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pixiewps_attack_{timestamp}.json"
        filepath = os.path.join(self.results_dir, filename)

        try:
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2)
            self.logger.info(f"Results saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")

    def get_version(self) -> Optional[str]:
        """Get pixiewps version"""
        if not self.check_binary():
            return None

        try:
            result = subprocess.run([self.pixiewps_path, "-V"],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            self.logger.error(f"Failed to get pixiewps version: {e}")

        return None

    def list_recent_results(self, limit: int = 10) -> List[Dict]:
        """List recent attack results"""
        results = []

        try:
            result_files = sorted(
                [f for f in os.listdir(self.results_dir) if f.endswith('.json')],
                reverse=True
            )[:limit]

            for filename in result_files:
                filepath = os.path.join(self.results_dir, filename)
                try:
                    with open(filepath) as f:
                        result_data = json.load(f)
                        results.append({
                            "filename": filename,
                            "timestamp": result_data.get("timestamp"),
                            "status": result_data.get("status"),
                            "wps_pin": result_data.get("wps_pin"),
                            "psk": result_data.get("psk")
                        })
                except Exception as e:
                    self.logger.error(f"Failed to read result file {filename}: {e}")

        except Exception as e:
            self.logger.error(f"Failed to list results: {e}")

        return results

# Test function
def test_pixiewps_wrapper():
    """Test function for pixiewps wrapper"""
    wrapper = PixiewpsWrapper()

    print("Testing Pixiewps Wrapper...")
    print(f"Binary available: {wrapper.check_binary()}")

    version = wrapper.get_version()
    if version:
        print(f"Version: {version}")

    # Example test with dummy data (will fail but tests the wrapper)
    test_result = wrapper.run_attack(
        pke="dummy_pke",
        pkr="dummy_pkr",
        e_hash1="dummy_hash1",
        e_hash2="dummy_hash2",
        authkey="dummy_authkey",
        e_nonce="dummy_nonce"
    )

    print(f"Test result: {test_result['status']}")
    return test_result

if __name__ == "__main__":
    test_pixiewps_wrapper()
