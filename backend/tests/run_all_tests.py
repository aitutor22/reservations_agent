#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run all test scripts in the tests directory
"""

import sys
import os
# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess

def run_test(test_file):
    """Run a single test file"""
    print(f"\n{'='*60}")
    print(f"Running: {test_file}")
    print('='*60)
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode != 0:
            print(f"❌ Test failed with return code: {result.returncode}")
            return False
        else:
            print(f"✅ Test passed")
            return True
            
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("RUNNING ALL BACKEND TESTS")
    print("="*60)
    
    test_files = [
        "test_agents.py",
        "test_personality.py",
        # "test_handoff.py",  # Requires async session
        # "test_reservation_api.py",  # Requires server running
    ]
    
    print("\nNote: Skipping tests that require the server to be running")
    print("To run those tests individually:")
    print("  - python tests/test_handoff.py (requires async session)")
    print("  - python tests/test_reservation_api.py (requires server)")
    
    results = []
    for test_file in test_files:
        passed = run_test(test_file)
        results.append((test_file, passed))
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_file, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_file:30} {status}")
    
    total = len(results)
    passed_count = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {passed_count}/{total} tests passed")
    
    return all(passed for _, passed in results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)