#!/usr/bin/env python3
"""
Test Runner for HeatGuard Test Suite
====================================

Comprehensive test runner with multiple execution modes:
- Full test suite execution
- Category-based test execution (unit, integration, performance, etc.)
- Coverage reporting and analysis
- Test result summarization and reporting
- CI/CD integration support

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit            # Run only unit tests
    python run_tests.py --integration     # Run only integration tests
    python run_tests.py --performance     # Run performance tests
    python run_tests.py --security        # Run security tests
    python run_tests.py --compliance      # Run OSHA compliance tests
    python run_tests.py --coverage        # Run with detailed coverage
    python run_tests.py --fast            # Skip slow tests
    python run_tests.py --parallel        # Run tests in parallel
"""

import argparse
import sys
import os
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path


class HeatGuardTestRunner:
    """Test runner for HeatGuard comprehensive test suite."""

    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.project_root = self.test_dir.parent
        self.coverage_threshold = 90
        self.results = {
            'start_time': None,
            'end_time': None,
            'duration': None,
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'coverage_percent': 0,
            'test_categories': {}
        }

    def run_full_suite(self, parallel=False, coverage=True):
        """Run the complete test suite."""
        print("🔥 HeatGuard Predictive Safety System - Test Suite")
        print("=" * 60)
        print(f"Running comprehensive test suite...")
        print(f"Test directory: {self.test_dir}")
        print(f"Coverage threshold: {self.coverage_threshold}%")
        print()

        cmd = ["python", "-m", "pytest"]

        if parallel:
            cmd.extend(["-n", "auto"])
            print("🚀 Running tests in parallel mode")

        if coverage:
            cmd.extend([
                "--cov=app",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
                "--cov-report=xml:coverage.xml",
                f"--cov-fail-under={self.coverage_threshold}"
            ])

        cmd.extend(["--verbose", "--tb=short", "--durations=10"])

        return self._execute_tests(cmd, "Full Test Suite")

    def run_unit_tests(self):
        """Run unit tests only."""
        print("🔬 Running Unit Tests")
        print("-" * 30)

        cmd = [
            "python", "-m", "pytest", "-m", "unit",
            "--verbose", "--tb=short"
        ]

        return self._execute_tests(cmd, "Unit Tests")

    def run_integration_tests(self):
        """Run integration tests only."""
        print("🔗 Running Integration Tests")
        print("-" * 35)

        cmd = [
            "python", "-m", "pytest", "-m", "integration",
            "--verbose", "--tb=short"
        ]

        return self._execute_tests(cmd, "Integration Tests")

    def run_performance_tests(self):
        """Run performance tests only."""
        print("⚡ Running Performance Tests")
        print("-" * 32)

        cmd = [
            "python", "-m", "pytest", "-m", "performance",
            "--verbose", "--tb=short", "--durations=0"
        ]

        return self._execute_tests(cmd, "Performance Tests")

    def run_security_tests(self):
        """Run security tests only."""
        print("🔒 Running Security Tests")
        print("-" * 27)

        cmd = [
            "python", "-m", "pytest", "-m", "security",
            "--verbose", "--tb=short"
        ]

        return self._execute_tests(cmd, "Security Tests")

    def run_compliance_tests(self):
        """Run OSHA compliance tests only."""
        print("📋 Running OSHA Compliance Tests")
        print("-" * 37)

        cmd = [
            "python", "-m", "pytest", "-m", "compliance",
            "--verbose", "--tb=short"
        ]

        return self._execute_tests(cmd, "OSHA Compliance Tests")

    def run_fast_tests(self):
        """Run tests excluding slow tests."""
        print("🏃 Running Fast Tests (excluding slow)")
        print("-" * 40)

        cmd = [
            "python", "-m", "pytest", "-m", "not slow",
            "--verbose", "--tb=short"
        ]

        return self._execute_tests(cmd, "Fast Tests")

    def run_specific_test_file(self, test_file):
        """Run a specific test file."""
        print(f"📄 Running Specific Test File: {test_file}")
        print("-" * 50)

        test_path = self.test_dir / test_file
        if not test_path.exists():
            print(f"❌ Test file not found: {test_path}")
            return False

        cmd = [
            "python", "-m", "pytest", str(test_path),
            "--verbose", "--tb=short"
        ]

        return self._execute_tests(cmd, f"Test File: {test_file}")

    def _execute_tests(self, cmd, test_type):
        """Execute pytest command and capture results."""
        print(f"Command: {' '.join(cmd)}")
        print()

        self.results['start_time'] = datetime.now()
        start_time = time.time()

        try:
            # Change to project root directory
            os.chdir(self.project_root)

            # Execute pytest
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            end_time = time.time()
            self.results['end_time'] = datetime.now()
            self.results['duration'] = end_time - start_time

            # Parse results
            self._parse_test_results(result.stdout, result.stderr, test_type)

            # Print results
            self._print_results(result, test_type)

            return result.returncode == 0

        except Exception as e:
            print(f"❌ Error executing tests: {e}")
            return False

    def _parse_test_results(self, stdout, stderr, test_type):
        """Parse pytest output to extract results."""
        lines = stdout.split('\n') + stderr.split('\n')

        for line in lines:
            if "passed" in line and ("failed" in line or "error" in line):
                # Parse summary line like "10 passed, 2 failed, 1 skipped"
                parts = line.split(',')
                for part in parts:
                    part = part.strip()
                    if 'passed' in part:
                        self.results['passed'] = int(part.split()[0])
                    elif 'failed' in part:
                        self.results['failed'] = int(part.split()[0])
                    elif 'skipped' in part:
                        self.results['skipped'] = int(part.split()[0])

            elif "coverage" in line.lower() and "%" in line:
                # Parse coverage line
                try:
                    coverage_str = line.split('%')[0].split()[-1]
                    self.results['coverage_percent'] = float(coverage_str)
                except:
                    pass

        self.results['total_tests'] = (
            self.results['passed'] +
            self.results['failed'] +
            self.results['skipped']
        )

        self.results['test_categories'][test_type] = {
            'passed': self.results['passed'],
            'failed': self.results['failed'],
            'skipped': self.results['skipped']
        }

    def _print_results(self, result, test_type):
        """Print test execution results."""
        print("\n" + "=" * 60)
        print(f"📊 {test_type} Results")
        print("=" * 60)

        if result.returncode == 0:
            print("✅ Tests PASSED")
        else:
            print("❌ Tests FAILED")

        print(f"Duration: {self.results['duration']:.2f} seconds")
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"Passed: {self.results['passed']}")
        print(f"Failed: {self.results['failed']}")
        print(f"Skipped: {self.results['skipped']}")

        if self.results['coverage_percent'] > 0:
            print(f"Coverage: {self.results['coverage_percent']:.1f}%")

        # Print stdout if there are failures or verbose mode
        if result.returncode != 0 and result.stdout:
            print("\n📋 Test Output:")
            print("-" * 40)
            print(result.stdout)

        if result.stderr:
            print("\n⚠️  Error Output:")
            print("-" * 40)
            print(result.stderr)

        print()

    def generate_test_report(self):
        """Generate a comprehensive test report."""
        report_file = self.test_dir / "test_report.json"

        report_data = {
            'test_run': {
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': self.results['duration'],
                'python_version': sys.version,
                'test_directory': str(self.test_dir),
                'coverage_threshold': self.coverage_threshold
            },
            'results': self.results,
            'test_files': self._get_test_file_info(),
            'coverage': self._get_coverage_info()
        }

        try:
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            print(f"📄 Test report saved to: {report_file}")
        except Exception as e:
            print(f"⚠️  Could not save test report: {e}")

    def _get_test_file_info(self):
        """Get information about test files."""
        test_files = list(self.test_dir.glob("test_*.py"))

        file_info = {}
        for test_file in test_files:
            file_info[test_file.name] = {
                'path': str(test_file),
                'size_bytes': test_file.stat().st_size,
                'modified': datetime.fromtimestamp(test_file.stat().st_mtime).isoformat()
            }

        return file_info

    def _get_coverage_info(self):
        """Get coverage information if available."""
        coverage_file = self.project_root / "coverage.xml"

        if coverage_file.exists():
            return {
                'coverage_file': str(coverage_file),
                'html_report': str(self.project_root / "htmlcov" / "index.html"),
                'threshold_met': self.results['coverage_percent'] >= self.coverage_threshold
            }

        return None

    def check_test_requirements(self):
        """Check if all test requirements are met."""
        print("🔍 Checking Test Requirements")
        print("-" * 32)

        requirements = [
            ("Python version", sys.version_info >= (3, 8)),
            ("Test directory exists", self.test_dir.exists()),
            ("pytest available", self._check_pytest_available()),
            ("Test files present", len(list(self.test_dir.glob("test_*.py"))) > 0)
        ]

        all_ok = True
        for name, check in requirements:
            status = "✅" if check else "❌"
            print(f"{status} {name}")
            if not check:
                all_ok = False

        print()
        return all_ok

    def _check_pytest_available(self):
        """Check if pytest is available."""
        try:
            subprocess.run(["python", "-m", "pytest", "--version"],
                          capture_output=True, check=True)
            return True
        except:
            return False

    def print_test_categories(self):
        """Print available test categories."""
        print("📂 Available Test Categories:")
        print("-" * 32)

        categories = {
            "unit": "Individual component tests",
            "integration": "Component interaction tests",
            "performance": "Performance and load tests (<200ms requirement)",
            "security": "Authentication and security tests",
            "compliance": "OSHA compliance and regulatory tests",
            "slow": "Long-running tests (>5 seconds)"
        }

        for category, description in categories.items():
            print(f"  {category:12} - {description}")

        print()

        # Count tests in each category
        test_files = {
            "test_api_endpoints.py": "API endpoint functionality",
            "test_heat_predictor.py": "ML model validation",
            "test_auth.py": "Authentication and security",
            "test_performance.py": "Performance requirements",
            "test_integration.py": "End-to-end workflows",
            "test_compliance.py": "OSHA compliance",
            "test_services.py": "Service layer logic",
            "test_utils.py": "Utility functions"
        }

        print("📄 Available Test Files:")
        print("-" * 25)
        for filename, description in test_files.items():
            test_path = self.test_dir / filename
            exists = "✅" if test_path.exists() else "❌"
            print(f"  {exists} {filename:20} - {description}")

        print()


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="HeatGuard Test Suite Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py --unit            # Run unit tests only
  python run_tests.py --performance     # Run performance tests
  python run_tests.py --fast --parallel # Run fast tests in parallel
  python run_tests.py --file test_api_endpoints.py  # Run specific file
        """
    )

    parser.add_argument("--unit", action="store_true",
                       help="Run unit tests only")
    parser.add_argument("--integration", action="store_true",
                       help="Run integration tests only")
    parser.add_argument("--performance", action="store_true",
                       help="Run performance tests only")
    parser.add_argument("--security", action="store_true",
                       help="Run security tests only")
    parser.add_argument("--compliance", action="store_true",
                       help="Run OSHA compliance tests only")
    parser.add_argument("--fast", action="store_true",
                       help="Skip slow tests")
    parser.add_argument("--parallel", action="store_true",
                       help="Run tests in parallel")
    parser.add_argument("--no-coverage", action="store_true",
                       help="Disable coverage reporting")
    parser.add_argument("--file", type=str,
                       help="Run specific test file")
    parser.add_argument("--check", action="store_true",
                       help="Check test requirements only")
    parser.add_argument("--list", action="store_true",
                       help="List available test categories and files")
    parser.add_argument("--report", action="store_true",
                       help="Generate detailed test report")

    args = parser.parse_args()

    runner = HeatGuardTestRunner()

    # Handle special actions first
    if args.list:
        runner.print_test_categories()
        return 0

    if args.check:
        if runner.check_test_requirements():
            print("✅ All test requirements met")
            return 0
        else:
            print("❌ Test requirements not met")
            return 1

    # Check requirements before running tests
    if not runner.check_test_requirements():
        print("❌ Cannot run tests - requirements not met")
        return 1

    # Determine which tests to run
    success = True
    coverage = not args.no_coverage

    if args.file:
        success = runner.run_specific_test_file(args.file)
    elif args.unit:
        success = runner.run_unit_tests()
    elif args.integration:
        success = runner.run_integration_tests()
    elif args.performance:
        success = runner.run_performance_tests()
    elif args.security:
        success = runner.run_security_tests()
    elif args.compliance:
        success = runner.run_compliance_tests()
    elif args.fast:
        success = runner.run_fast_tests()
    else:
        # Run full suite
        success = runner.run_full_suite(parallel=args.parallel, coverage=coverage)

    # Generate report if requested
    if args.report:
        runner.generate_test_report()

    # Final status
    if success:
        print("🎉 Test execution completed successfully!")
        return 0
    else:
        print("💥 Test execution failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())