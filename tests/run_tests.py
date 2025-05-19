#!/usr/bin/env python3
"""
MODULE: modules/project_management/tests/run_tests.py
PURPOSE: Simple test runner for project management module tests
DEPENDENCIES:
    - unittest: Standard library testing framework
    - pathlib: For path manipulation

This script provides a simple way to run all or selected tests for the
project management module without requiring pytest or complex imports.
It's particularly useful for standalone testing during development.
"""

import unittest
import sys
import os
import argparse
from pathlib import Path


def main():
    """Run the specified tests."""
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Run project management tests')
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('files', nargs='*', help='Specific test files to run')
    
    args = parser.parse_args()
    
    # Determine current directory and test paths
    current_dir = Path(__file__).parent
    unit_dir = current_dir / 'unit'
    integration_dir = current_dir / 'integration'
    
    # Add parent directories to path to enable imports
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Configure test loader
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # If specific files are provided, run only those
    if args.files:
        for file_path in args.files:
            path = Path(file_path)
            if not path.is_absolute():
                path = current_dir / path
            
            # Check if the file exists
            if path.exists():
                # Load tests from the file
                print(f"Loading tests from: {path}")
                
                # Handle both module paths and file paths
                if path.is_file():
                    # Convert file path to module path
                    module_path = str(path.relative_to(project_root)).replace('/', '.').replace('\\', '.')
                    if module_path.endswith('.py'):
                        module_path = module_path[:-3]
                    suite.addTests(loader.loadTestsFromName(module_path))
                else:
                    suite.addTests(loader.discover(path, pattern='test_*.py'))
            else:
                print(f"Warning: Test file not found: {path}")
    else:
        # Determine which test types to run
        run_unit = args.unit or not (args.unit or args.integration)
        run_integration = args.integration or not (args.unit or args.integration)
        
        # Load unit tests
        if run_unit:
            print(f"Loading unit tests from: {unit_dir}")
            suite.addTests(loader.discover(unit_dir, pattern='test_*.py'))
        
        # Load integration tests
        if run_integration:
            print(f"Loading integration tests from: {integration_dir}")
            suite.addTests(loader.discover(integration_dir, pattern='test_*.py'))
    
    # Run the tests
    verbosity = 2 if args.verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    # Return non-zero exit code if tests failed
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main() 