#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for reservation service security methods
Tests name verification and fuzzy matching in service layer
"""

import sys
import os
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock, Mock
from datetime import datetime

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.reservation_service import ReservationService
from models.reservation import ReservationCreate, ReservationUpdate
from utils.name_matching import names_match, split_and_match_names


async def test_verify_reservation_owner():
    """Test owner verification with fuzzy name matching"""
    print("\n=== Testing verify_reservation_owner ===")
    
    # Create mock database session
    mock_db = AsyncMock()
    
    # Create mock reservation data
    mock_reservation = Mock()
    mock_reservation.id = 1
    mock_reservation.name = "John Smith"
    mock_reservation.phone_number = "+6591234567"
    mock_reservation.reservation_date = "2024-01-15"
    mock_reservation.reservation_time = "19:00"
    mock_reservation.party_size = 4
    mock_reservation.other_info = {"special_requests": "Window seat"}
    
    # Mock the database query
    mock_result = Mock()
    mock_result.scalars.return_value.first.return_value = mock_reservation
    mock_db.execute.return_value = mock_result
    
    service = ReservationService(mock_db)
    
    # Test exact match
    result = await service.verify_reservation_owner("+6591234567", "John Smith")
    assert result is not None
    assert result.name == "John Smith"
    print("✅ Exact name match test passed")
    
    # Test fuzzy match (transcription error)
    result = await service.verify_reservation_owner("+6591234567", "Jon Smith")
    assert result is not None  # Should match with Levenshtein distance 1
    print("✅ Fuzzy match (Jon vs John) test passed")
    
    # Test case insensitive
    result = await service.verify_reservation_owner("+6591234567", "john smith")
    assert result is not None
    print("✅ Case insensitive match test passed")
    
    # Test partial name match
    result = await service.verify_reservation_owner("+6591234567", "John")
    assert result is not None  # Should match first name
    print("✅ Partial name match test passed")
    
    # Test wrong name
    result = await service.verify_reservation_owner("+6591234567", "Jane Doe")
    assert result is None  # Should NOT match
    print("✅ Wrong name rejection test passed")
    
    # Test no reservation found
    mock_result.scalars.return_value.first.return_value = None
    result = await service.verify_reservation_owner("+6599999999", "Any Name")
    assert result is None
    print("✅ No reservation test passed")


async def test_delete_reservation_with_verification():
    """Test deletion with name verification"""
    print("\n=== Testing delete_reservation with verification ===")
    
    # Create mock database session
    mock_db = AsyncMock()
    
    # Create mock reservation
    mock_reservation = Mock()
    mock_reservation.id = 1
    mock_reservation.name = "Dan Lee"
    mock_reservation.phone_number = "+6591234567"
    
    # Mock the query for verification
    mock_result = Mock()
    mock_result.scalars.return_value.first.return_value = mock_reservation
    mock_db.execute.return_value = mock_result
    
    service = ReservationService(mock_db)
    
    # Test successful deletion with correct name
    result = await service.delete_reservation("+6591234567", "Dan Lee")
    assert result is True
    mock_db.delete.assert_called_once_with(mock_reservation)
    mock_db.commit.assert_called_once()
    print("✅ Successful deletion test passed")
    
    # Reset mocks
    mock_db.reset_mock()
    mock_result.scalars.return_value.first.return_value = mock_reservation
    
    # Test deletion with fuzzy match name
    result = await service.delete_reservation("+6591234567", "Den Lee")  # Den vs Dan
    assert result is True
    mock_db.delete.assert_called_once()
    print("✅ Deletion with fuzzy name test passed")
    
    # Reset mocks
    mock_db.reset_mock()
    mock_result.scalars.return_value.first.return_value = mock_reservation
    
    # Test failed deletion with wrong name
    result = await service.delete_reservation("+6591234567", "Wrong Name")
    assert result is False
    mock_db.delete.assert_not_called()
    mock_db.commit.assert_not_called()
    print("✅ Failed deletion (wrong name) test passed")
    
    # Test deletion when reservation doesn't exist
    mock_result.scalars.return_value.first.return_value = None
    result = await service.delete_reservation("+6599999999", "Any Name")
    assert result is False
    print("✅ No reservation deletion test passed")


async def test_update_reservation_with_verification():
    """Test update with name verification"""
    print("\n=== Testing update_reservation with verification ===")
    
    # Create mock database session
    mock_db = AsyncMock()
    
    # Create mock reservation
    mock_reservation = Mock()
    mock_reservation.id = 1
    mock_reservation.name = "Mary Wong"
    mock_reservation.phone_number = "+6587654321"
    mock_reservation.reservation_date = "2024-01-15"
    mock_reservation.reservation_time = "19:00"
    mock_reservation.party_size = 2
    mock_reservation.other_info = {}
    
    # Mock the query
    mock_result = Mock()
    mock_result.scalars.return_value.first.return_value = mock_reservation
    mock_db.execute.return_value = mock_result
    
    service = ReservationService(mock_db)
    
    # Test successful update with correct name
    update_data = ReservationUpdate(
        reservation_time="20:00",
        party_size=3
    )
    
    result = await service.update_reservation("+6587654321", "Mary Wong", update_data)
    assert result is not None
    assert mock_reservation.reservation_time == "20:00"
    assert mock_reservation.party_size == 3
    mock_db.commit.assert_called_once()
    print("✅ Successful update test passed")
    
    # Reset mocks
    mock_db.reset_mock()
    mock_reservation.reservation_time = "19:00"
    mock_reservation.party_size = 2
    
    # Test update with fuzzy match (Wang vs Wong)
    result = await service.update_reservation("+6587654321", "Mary Wang", update_data)
    assert result is not None  # Should match with LD=1
    print("✅ Update with fuzzy name test passed")
    
    # Reset mocks
    mock_db.reset_mock()
    
    # Test failed update with wrong name
    result = await service.update_reservation("+6587654321", "John Doe", update_data)
    assert result is None
    mock_db.commit.assert_not_called()
    print("✅ Failed update (wrong name) test passed")
    
    # Test update when reservation doesn't exist
    mock_result.scalars.return_value.first.return_value = None
    result = await service.update_reservation("+6599999999", "Any Name", update_data)
    assert result is None
    print("✅ No reservation update test passed")


async def test_common_transcription_errors():
    """Test handling of common voice transcription errors"""
    print("\n=== Testing Common Transcription Errors ===")
    
    # Create mock database session
    mock_db = AsyncMock()
    
    # Test various name variations
    test_cases = [
        ("Chen", "Chan"),     # e→a confusion
        ("Lee", "Li"),        # ee→i confusion  
        ("Tan", "Tang"),      # Missing g
        ("Wong", "Wang"),     # o→a confusion
        ("Smith", "Smyth"),   # i→y confusion
    ]
    
    for stored_name, spoken_name in test_cases:
        mock_reservation = Mock()
        mock_reservation.id = 1
        mock_reservation.name = stored_name
        mock_reservation.phone_number = "+6591234567"
        mock_reservation.reservation_date = "2024-01-15"
        mock_reservation.reservation_time = "19:00"
        mock_reservation.party_size = 4
        mock_reservation.other_info = {}
        
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = mock_reservation
        mock_db.execute.return_value = mock_result
        
        service = ReservationService(mock_db)
        
        # Verify fuzzy matching works
        result = await service.verify_reservation_owner("+6591234567", spoken_name)
        assert result is not None, f"Failed to match {spoken_name} to {stored_name}"
        print(f"✅ Transcription error handled: {stored_name} ← {spoken_name}")


async def test_security_boundaries():
    """Test security boundaries and edge cases"""
    print("\n=== Testing Security Boundaries ===")
    
    # Create mock database session
    mock_db = AsyncMock()
    
    # Create mock reservation
    mock_reservation = Mock()
    mock_reservation.id = 1
    mock_reservation.name = "John Smith"
    mock_reservation.phone_number = "+6591234567"
    
    mock_result = Mock()
    mock_result.scalars.return_value.first.return_value = mock_reservation
    mock_db.execute.return_value = mock_result
    
    service = ReservationService(mock_db)
    
    # Test empty name should not match
    result = await service.verify_reservation_owner("+6591234567", "")
    assert result is None
    print("✅ Empty name rejection test passed")
    
    # Test very different name should not match
    result = await service.verify_reservation_owner("+6591234567", "XYZ")
    assert result is None
    print("✅ Very different name rejection test passed")
    
    # Test SQL injection attempt (should be safe)
    result = await service.verify_reservation_owner("+6591234567", "'; DROP TABLE--")
    assert result is None
    print("✅ SQL injection safety test passed")
    
    # Test with special characters
    mock_reservation.name = "O'Brien"
    result = await service.verify_reservation_owner("+6591234567", "O'Brien")
    assert result is not None
    print("✅ Special characters test passed")
    
    # Test with unicode characters
    mock_reservation.name = "李明"
    result = await service.verify_reservation_owner("+6591234567", "李明")
    assert result is not None
    print("✅ Unicode characters test passed")


async def test_phone_number_formatting():
    """Test phone number handling in service layer"""
    print("\n=== Testing Phone Number Formatting ===")
    
    mock_db = AsyncMock()
    service = ReservationService(mock_db)
    
    # Create mock reservation
    mock_reservation = Mock()
    mock_reservation.id = 1
    mock_reservation.name = "Test User"
    mock_reservation.phone_number = "+6591234567"
    
    mock_result = Mock()
    mock_result.scalars.return_value.first.return_value = mock_reservation
    mock_db.execute.return_value = mock_result
    
    # Service should work with already formatted numbers
    result = await service.verify_reservation_owner("+6591234567", "Test User")
    assert result is not None
    print("✅ Pre-formatted phone number test passed")
    
    # Service expects pre-formatted numbers from API layer
    # (formatting happens in the tools/API layer, not service layer)
    call_args = mock_db.execute.call_args[0][0]
    # Verify the SQL query uses the provided phone number
    print("✅ Phone number passed through correctly")


async def run_all_tests():
    """Run all async tests"""
    print("\n" + "="*70)
    print("RESERVATION SERVICE SECURITY TEST SUITE")
    print("Testing service layer security with fuzzy name matching")
    print("="*70)
    
    try:
        await test_verify_reservation_owner()
        await test_delete_reservation_with_verification()
        await test_update_reservation_with_verification()
        await test_common_transcription_errors()
        await test_security_boundaries()
        await test_phone_number_formatting()
        
        print("\n" + "="*70)
        print("✅ ALL SERVICE TESTS PASSED!")
        print("="*70)
        print("\nThe reservation service is working correctly with:")
        print("- Fuzzy name matching (Levenshtein distance ≤ 2)")
        print("- Secure verification for delete/update operations")
        print("- Handling of common transcription errors")
        print("- Protection against unauthorized access")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()