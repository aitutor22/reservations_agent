#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for name matching functionality
Tests Levenshtein distance calculation and fuzzy name matching
"""

import sys
import os
# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.name_matching import (
    calculate_levenshtein_distance,
    normalize_name,
    names_match,
    split_and_match_names
)


def test_levenshtein_distance():
    """Test Levenshtein distance calculation"""
    print("\n=== Testing Levenshtein Distance ===")
    
    test_cases = [
        ("hello", "hello", 0),  # Exact match
        ("hello", "helo", 1),   # One deletion
        ("hello", "helllo", 1), # One insertion
        ("hello", "hallo", 1),  # One substitution
        ("Dan", "Dan", 0),      # Exact match
        ("Dan", "Don", 1),      # One substitution
        ("Dan", "Daniel", 3),   # Three insertions
        ("John", "Jon", 1),     # One deletion
        ("Smith", "Smyth", 1),  # One substitution
        ("", "test", 4),        # Empty string
        ("test", "", 4),        # Empty string
    ]
    
    print("\n{:<15} {:<15} {:<10} {:<10} {:<10}".format(
        "String 1", "String 2", "Expected", "Actual", "Result"
    ))
    print("-" * 65)
    
    all_passed = True
    for s1, s2, expected in test_cases:
        actual = calculate_levenshtein_distance(s1, s2)
        passed = actual == expected
        result = "✅" if passed else "❌"
        print(f"{s1:<15} {s2:<15} {expected:<10} {actual:<10} {result:<10}")
        if not passed:
            all_passed = False
    
    return all_passed


def test_normalize_name():
    """Test name normalization"""
    print("\n=== Testing Name Normalization ===")
    
    test_cases = [
        ("John Smith", "john smith"),
        ("  John  Smith  ", "john smith"),
        ("JOHN SMITH", "john smith"),
        ("John    Smith", "john smith"),
        ("  Dan  ", "dan"),
        ("李明", "李明"),  # Chinese characters should work
    ]
    
    print("\n{:<25} {:<25} {:<10}".format("Input", "Expected", "Result"))
    print("-" * 65)
    
    all_passed = True
    for input_name, expected in test_cases:
        actual = normalize_name(input_name)
        passed = actual == expected
        result = "✅" if passed else "❌"
        print(f"{input_name:<25} {expected:<25} {result:<10}")
        if not passed:
            all_passed = False
            print(f"  Actual: '{actual}'")
    
    return all_passed


def test_names_match():
    """Test fuzzy name matching"""
    print("\n=== Testing Fuzzy Name Matching ===")
    
    test_cases = [
        # (provided, stored, max_distance, should_match)
        ("Dan", "Dan", 2, True),           # Exact match
        ("Dan", "Don", 2, True),            # 1 char diff
        ("Dan", "Daniel", 2, False),        # 3 char diff (too many)
        ("John Smith", "John Smith", 2, True),  # Exact match
        ("John Smith", "john smith", 2, True),  # Case insensitive
        ("Jon Smith", "John Smith", 2, True),   # 1 char diff
        ("John Smyth", "John Smith", 2, True),  # 1 char diff
        ("John", "John Smith", 2, True),        # Contained name
        ("Smith", "John Smith", 2, True),       # Contained name
        ("Jo", "John Smith", 2, False),         # Too short to be contained
        ("Mary Lee", "Mary Li", 2, True),       # 2 char diff
        ("Mary Lee", "Marie Li", 2, False),     # 3 char diff
    ]
    
    print("\n{:<20} {:<20} {:<8} {:<10} {:<10} {:<10}".format(
        "Provided", "Stored", "MaxDist", "Expected", "Actual", "Result"
    ))
    print("-" * 85)
    
    all_passed = True
    for provided, stored, max_dist, should_match in test_cases:
        actual = names_match(provided, stored, max_dist)
        passed = actual == should_match
        result = "✅" if passed else "❌"
        expected = "Match" if should_match else "No Match"
        actual_str = "Match" if actual else "No Match"
        print(f"{provided:<20} {stored:<20} {max_dist:<8} {expected:<10} {actual_str:<10} {result:<10}")
        if not passed:
            all_passed = False
    
    return all_passed


def test_split_and_match_names():
    """Test enhanced name matching with splitting"""
    print("\n=== Testing Split Name Matching ===")
    
    test_cases = [
        # (provided, stored, should_match)
        ("Dan", "Dan Smith", True),        # First name match
        ("Smith", "Dan Smith", True),      # Last name match
        ("Daniel", "Dan Smith", False),    # Too different
        ("Dan S", "Dan Smith", True),      # Partial last name
        ("D Smith", "Dan Smith", True),    # Partial first name
        ("John", "John Lee", True),        # First name match
        ("Lee", "John Lee", True),         # Last name match
        ("John Lee", "John", True),        # Full name vs first
        ("Mary Jane", "Mary", True),       # Multi-part vs single
        ("Robert", "Bob Smith", False),    # Different names
    ]
    
    print("\n{:<20} {:<20} {:<10} {:<10} {:<10}".format(
        "Provided", "Stored", "Expected", "Actual", "Result"
    ))
    print("-" * 75)
    
    all_passed = True
    for provided, stored, should_match in test_cases:
        actual = split_and_match_names(provided, stored)
        passed = actual == should_match
        result = "✅" if passed else "❌"
        expected = "Match" if should_match else "No Match"
        actual_str = "Match" if actual else "No Match"
        print(f"{provided:<20} {stored:<20} {expected:<10} {actual_str:<10} {result:<10}")
        if not passed:
            all_passed = False
    
    return all_passed


def test_voice_transcription_errors():
    """Test handling of common voice transcription errors"""
    print("\n=== Testing Voice Transcription Error Handling ===")
    
    test_cases = [
        # Common transcription errors
        ("Dan", "Den", True),              # a→e confusion
        ("John", "Jon", True),              # Missing h
        ("Smith", "Smyth", True),           # i→y confusion
        ("Lee", "Li", True),                # ee→i confusion
        ("Wong", "Wang", True),             # o→a confusion
        ("Chen", "Chan", True),             # e→a confusion
        ("Tan", "Tang", True),              # Missing g
        ("michael", "Michelle", False),     # Too different
    ]
    
    print("\n{:<20} {:<20} {:<30} {:<10}".format(
        "Spoken", "Stored", "Scenario", "Result"
    ))
    print("-" * 85)
    
    for provided, stored, should_match in test_cases:
        actual = split_and_match_names(provided, stored, max_distance=2)
        passed = actual == should_match
        result = "✅" if passed else "❌"
        expected = "Match" if should_match else "No Match"
        scenario = f"Transcription error ({expected})"
        print(f"{provided:<20} {stored:<20} {scenario:<30} {result:<10}")
    
    return True


def main():
    """Run all tests"""
    print("\n" + "="*85)
    print("NAME MATCHING TEST SUITE")
    print("Testing fuzzy name matching for reservation verification")
    print("="*85)
    
    test_results = []
    
    # Run each test
    test_results.append(("Levenshtein Distance", test_levenshtein_distance()))
    test_results.append(("Name Normalization", test_normalize_name()))
    test_results.append(("Fuzzy Name Matching", test_names_match()))
    test_results.append(("Split Name Matching", test_split_and_match_names()))
    test_voice_transcription_errors()  # Informational only
    
    # Summary
    print("\n" + "="*85)
    print("TEST SUMMARY")
    print("="*85)
    
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:30} {status}")
    
    all_passed = all(passed for _, passed in test_results)
    
    if all_passed:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed. Please review the output above.")
    
    print("\nNote: This fuzzy matching helps handle voice transcription errors")
    print("while maintaining security for reservation modifications.")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)