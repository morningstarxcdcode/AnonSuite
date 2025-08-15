#!/usr/bin/env python3
"""
AnonSuite Test Runner
Comprehensive test execution with reporting and coverage
"""

import sys
import os
import subprocess
import argparse
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

class TestRunner:
    """Test runner with comprehensive reporting"""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.project_root = self.test_dir.parent
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "summary": {},
            "details": {},
            "coverage": {},
            "errors": []
        }
    
    def run_unit_tests(self, verbose=False):
        """Run unit tests"""
        print("=" * 60)
        print("RUNNING UNIT TESTS")
        print("=" * 60)
        
        cmd = [
            "/opt/homebrew/bin/pytest",
            str(self.test_dir / "unit"),
            "-v" if verbose else "-q",
            "--tb=short",
            "-m", "unit"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            self.results["details"]["unit_tests"] = {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            if result.returncode == 0:
                print("✓ Unit tests PASSED")
                self.results["summary"]["unit_tests"] = "PASSED"
            else:
                print("✗ Unit tests FAILED")
                self.results["summary"]["unit_tests"] = "FAILED"
                print(result.stdout)
                print(result.stderr)
                
        except Exception as e:
            print(f"✗ Error running unit tests: {e}")
            self.results["errors"].append(f"Unit tests error: {e}")
            self.results["summary"]["unit_tests"] = "ERROR"
    
    def run_integration_tests(self, verbose=False):
        """Run integration tests"""
        print("\n" + "=" * 60)
        print("RUNNING INTEGRATION TESTS")
        print("=" * 60)
        
        cmd = [
            "/opt/homebrew/bin/pytest",
            str(self.test_dir / "integration"),
            "-v" if verbose else "-q",
            "--tb=short",
            "-m", "integration"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            self.results["details"]["integration_tests"] = {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            if result.returncode == 0:
                print("✓ Integration tests PASSED")
                self.results["summary"]["integration_tests"] = "PASSED"
            else:
                print("✗ Integration tests FAILED")
                self.results["summary"]["integration_tests"] = "FAILED"
                print(result.stdout)
                print(result.stderr)
                
        except Exception as e:
            print(f"✗ Error running integration tests: {e}")
            self.results["errors"].append(f"Integration tests error: {e}")
            self.results["summary"]["integration_tests"] = "ERROR"
    
    def run_security_tests(self, verbose=False):
        """Run security tests"""
        print("\n" + "=" * 60)
        print("RUNNING SECURITY TESTS")
        print("=" * 60)
        
        cmd = [
            "/opt/homebrew/bin/pytest",
            str(self.test_dir / "security"),
            "-v" if verbose else "-q",
            "--tb=short",
            "-m", "security"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            self.results["details"]["security_tests"] = {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            if result.returncode == 0:
                print("✓ Security tests PASSED")
                self.results["summary"]["security_tests"] = "PASSED"
            else:
                print("✗ Security tests FAILED")
                self.results["summary"]["security_tests"] = "FAILED"
                print(result.stdout)
                print(result.stderr)
                
        except Exception as e:
            print(f"✗ Error running security tests: {e}")
            self.results["errors"].append(f"Security tests error: {e}")
            self.results["summary"]["security_tests"] = "ERROR"
    
    def run_linting(self):
        """Run code linting"""
        print("\n" + "=" * 60)
        print("RUNNING CODE LINTING")
        print("=" * 60)
        
        # Check if ruff is available
        try:
            subprocess.run(["ruff", "--version"], capture_output=True, check=True)
            linter = "ruff"
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                subprocess.run(["flake8", "--version"], capture_output=True, check=True)
                linter = "flake8"
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("⚠ No linter available (ruff or flake8)")
                self.results["summary"]["linting"] = "SKIPPED"
                return
        
        if linter == "ruff":
            cmd = ["ruff", "check", str(self.project_root / "src")]
        else:
            cmd = ["flake8", str(self.project_root / "src")]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.results["details"]["linting"] = {
                "linter": linter,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            if result.returncode == 0:
                print(f"✓ Linting ({linter}) PASSED")
                self.results["summary"]["linting"] = "PASSED"
            else:
                print(f"✗ Linting ({linter}) FAILED")
                self.results["summary"]["linting"] = "FAILED"
                print(result.stdout)
                
        except Exception as e:
            print(f"✗ Error running linting: {e}")
            self.results["errors"].append(f"Linting error: {e}")
            self.results["summary"]["linting"] = "ERROR"
    
    def run_type_checking(self):
        """Run type checking"""
        print("\n" + "=" * 60)
        print("RUNNING TYPE CHECKING")
        print("=" * 60)
        
        # Check if mypy is available
        try:
            subprocess.run(["mypy", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠ mypy not available, skipping type checking")
            self.results["summary"]["type_checking"] = "SKIPPED"
            return
        
        cmd = [
            "mypy",
            str(self.project_root / "src"),
            "--ignore-missing-imports",
            "--no-strict-optional"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.results["details"]["type_checking"] = {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            if result.returncode == 0:
                print("✓ Type checking PASSED")
                self.results["summary"]["type_checking"] = "PASSED"
            else:
                print("✗ Type checking FAILED")
                self.results["summary"]["type_checking"] = "FAILED"
                print(result.stdout)
                
        except Exception as e:
            print(f"✗ Error running type checking: {e}")
            self.results["errors"].append(f"Type checking error: {e}")
            self.results["summary"]["type_checking"] = "ERROR"
    
    def generate_coverage_report(self):
        """Generate test coverage report"""
        print("\n" + "=" * 60)
        print("GENERATING COVERAGE REPORT")
        print("=" * 60)
        
        # Check if coverage is available
        try:
            subprocess.run(["coverage", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠ coverage not available, skipping coverage report")
            self.results["summary"]["coverage"] = "SKIPPED"
            return
        
        # Run tests with coverage
        cmd = [
            "coverage", "run", "-m", "pytest",
            str(self.test_dir),
            "--tb=no", "-q"
        ]
        
        try:
            subprocess.run(cmd, cwd=self.project_root, check=True)
            
            # Generate coverage report
            result = subprocess.run(
                ["coverage", "report", "--format=json"],
                capture_output=True, text=True, cwd=self.project_root
            )
            
            if result.returncode == 0:
                coverage_data = json.loads(result.stdout)
                self.results["coverage"] = coverage_data
                
                total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)
                print(f"✓ Coverage report generated: {total_coverage:.1f}%")
                self.results["summary"]["coverage"] = f"{total_coverage:.1f}%"
            else:
                print("✗ Coverage report generation failed")
                self.results["summary"]["coverage"] = "FAILED"
                
        except Exception as e:
            print(f"✗ Error generating coverage report: {e}")
            self.results["errors"].append(f"Coverage error: {e}")
            self.results["summary"]["coverage"] = "ERROR"
    
    def save_results(self, output_file=None):
        """Save test results to file"""
        if output_file is None:
            output_file = self.project_root / "test_results.json"
        
        try:
            with open(output_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"\n📊 Test results saved to: {output_file}")
        except Exception as e:
            print(f"✗ Error saving results: {e}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        for test_type, status in self.results["summary"].items():
            status_symbol = {
                "PASSED": "✓",
                "FAILED": "✗", 
                "ERROR": "⚠",
                "SKIPPED": "⊝"
            }.get(status, "?")
            
            print(f"{status_symbol} {test_type.replace('_', ' ').title()}: {status}")
        
        if self.results["errors"]:
            print(f"\n⚠ {len(self.results['errors'])} error(s) encountered:")
            for error in self.results["errors"]:
                print(f"  • {error}")
        
        # Overall status
        failed_tests = [k for k, v in self.results["summary"].items() 
                       if v in ["FAILED", "ERROR"]]
        
        if failed_tests:
            print(f"\n❌ OVERALL: FAILED ({len(failed_tests)} test suite(s) failed)")
            return False
        else:
            print(f"\n✅ OVERALL: PASSED")
            return True

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="AnonSuite Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--security", action="store_true", help="Run security tests only")
    parser.add_argument("--lint", action="store_true", help="Run linting only")
    parser.add_argument("--type-check", action="store_true", help="Run type checking only")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--output", "-o", help="Output file for results")
    parser.add_argument("--all", action="store_true", help="Run all tests and checks")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # If no specific tests selected, run all
    if not any([args.unit, args.integration, args.security, args.lint, 
                args.type_check, args.coverage]) or args.all:
        args.unit = args.integration = args.security = True
        args.lint = args.type_check = args.coverage = True
    
    # Run selected tests
    if args.unit:
        runner.run_unit_tests(args.verbose)
    
    if args.integration:
        runner.run_integration_tests(args.verbose)
    
    if args.security:
        runner.run_security_tests(args.verbose)
    
    if args.lint:
        runner.run_linting()
    
    if args.type_check:
        runner.run_type_checking()
    
    if args.coverage:
        runner.generate_coverage_report()
    
    # Print summary and save results
    success = runner.print_summary()
    runner.save_results(args.output)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
