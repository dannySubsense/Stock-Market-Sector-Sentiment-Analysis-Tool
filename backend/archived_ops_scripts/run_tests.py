#!/usr/bin/env python3
"""
Test runner script for Market Sector Sentiment Analysis Tool
Provides convenient commands for running different test suites
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}\n")

    result = subprocess.run(command, shell=True, capture_output=False)

    if result.returncode != 0:
        print(f"\n❌ {description} FAILED")
        return False
    else:
        print(f"\n✅ {description} PASSED")
        return True


def main():
    """Main test runner function"""
    if len(sys.argv) < 2:
        print("Usage: python run_tests.py <test_suite>")
        print("\nAvailable test suites:")
        print("  all              - Run all tests")
        print("  unit             - Run unit tests only")
        print("  integration      - Run integration tests only")
        print("  slice1a          - Run Slice 1A tests only")
        print("  slice1b          - Run Slice 1B tests only")
        print("  health           - Run health check tests")
        print("  sectors          - Run sector tests")
        print("  stocks           - Run stock tests")
        print("  performance      - Run performance tests")
        print("  coverage         - Run tests with coverage report")
        print("  quick            - Run quick test suite (unit + slice1a)")
        return 1

    test_suite = sys.argv[1].lower()

    # Change to backend directory
    os.chdir(Path(__file__).parent)

    if test_suite == "all":
        return run_command("pytest tests/ -v", "All Tests")

    elif test_suite == "unit":
        return run_command("pytest tests/unit/ -v -m unit", "Unit Tests")

    elif test_suite == "integration":
        return run_command(
            "pytest tests/integration/ -v -m integration", "Integration Tests"
        )

    elif test_suite == "slice1a":
        return run_command("pytest tests/slice1a/ -v -m slice1a", "Slice 1A Tests")

    elif test_suite == "slice1b":
        return run_command("pytest tests/slice1b/ -v -m slice1b", "Slice 1B Tests")

    elif test_suite == "health":
        return run_command(
            "pytest tests/unit/test_health_routes.py -v", "Health Check Tests"
        )

    elif test_suite == "sectors":
        return run_command(
            "pytest tests/unit/test_sectors_routes.py -v", "Sector Tests"
        )

    elif test_suite == "stocks":
        return run_command("pytest tests/unit/test_stocks_routes.py -v", "Stock Tests")

    elif test_suite == "performance":
        return run_command("pytest tests/ -v -m performance", "Performance Tests")

    elif test_suite == "coverage":
        return run_command(
            "pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing",
            "Tests with Coverage",
        )

    elif test_suite == "quick":
        success1 = run_command("pytest tests/unit/ -v -m unit", "Unit Tests")
        success2 = run_command("pytest tests/slice1a/ -v -m slice1a", "Slice 1A Tests")
        return success1 and success2

    else:
        print(f"Unknown test suite: {test_suite}")
        return 1


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
