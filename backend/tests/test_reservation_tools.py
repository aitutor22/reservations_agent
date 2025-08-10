#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for reservation tools with security features
Tests delete and modify operations with name verification
"""

import sys
import os
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realtime_tools.reservation import (
    _lookup_reservation_async,
    _delete_reservation_async,
    _modify_reservation_async,
    _make_reservation_async,
    check_availability
)


class MockResponse:
    """Mock HTTP response for testing"""
    def __init__(self, status_code, json_data=None):
        self.status_code = status_code
        self._json_data = json_data or {}
    
    def json(self):
        return self._json_data


async def test_lookup_reservation():
    """Test reservation lookup functionality"""
    print("\n=== Testing Lookup Reservation ===")
    
    # Mock successful lookup
    mock_response = MockResponse(200, {
        'name': 'John Smith',
        'phone_number': '+6591234567',
        'reservation_date': '2024-01-15',
        'reservation_time': '19:00',
        'party_size': 4,
        'other_info': {'special_requests': 'Window seat'}
    })
    
    with patch('realtime_tools.reservation.get_api_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        result = await _lookup_reservation_async("91234567")
        
        assert "✅ Reservation found!" in result
        assert "John Smith" in result
        assert "Window seat" in result
        print("✅ Successful lookup test passed")
    
    # Test not found
    mock_response = MockResponse(404)
    
    with patch('realtime_tools.reservation.get_api_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        result = await _lookup_reservation_async("99999999")
        
        assert "No reservation found" in result
        print("✅ Not found test passed")


async def test_delete_reservation():
    """Test secure reservation deletion with name verification"""
    print("\n=== Testing Delete Reservation ===")
    
    # Test successful deletion with correct credentials
    mock_response = MockResponse(200)
    
    with patch('realtime_tools.reservation.get_api_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.delete.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        result = await _delete_reservation_async("91234567", "John Smith")
        
        # Verify the call was made with both phone and name
        mock_client.delete.assert_called_once()
        call_args = mock_client.delete.call_args
        assert call_args[0][0] == "/api/reservations/+6591234567"
        assert call_args[1]['json'] == {"name": "John Smith"}
        
        assert "cancelled successfully" in result
        print("✅ Successful deletion test passed")
    
    # Test failed deletion (wrong name)
    mock_response = MockResponse(404)
    
    with patch('realtime_tools.reservation.get_api_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.delete.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        result = await _delete_reservation_async("91234567", "Wrong Name")
        
        assert "couldn't find a reservation with those details" in result
        print("✅ Failed deletion (wrong name) test passed")
    
    # Test generic error message doesn't reveal info
    mock_response = MockResponse(404)
    
    with patch('realtime_tools.reservation.get_api_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.delete.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        result1 = delete_reservation("99999999", "John Smith")  # Non-existent phone
        result2 = delete_reservation("91234567", "Wrong Name")  # Wrong name
        
        # Both should return the same generic message
        assert result1 == result2
        assert "couldn't find a reservation with those details" in result1
        print("✅ Generic error message test passed")


async def test_modify_reservation():
    """Test secure reservation modification with name verification"""
    print("\n=== Testing Modify Reservation ===")
    
    # Test successful modification
    mock_response = MockResponse(200, {
        'name': 'John Smith',
        'phone_number': '+6591234567',
        'reservation_date': '2024-01-16',
        'reservation_time': '20:00',
        'party_size': 6,
        'other_info': {'special_requests': 'Birthday celebration'}
    })
    
    with patch('realtime_tools.reservation.get_api_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.put.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        result = await _modify_reservation_async(
            phone="91234567",
            name="John Smith",
            new_date="2024-01-16",
            new_time="20:00",
            new_party_size=6,
            new_special_requests="Birthday celebration"
        )
        
        # Verify the call included verification name
        call_args = mock_client.put.call_args
        assert call_args[1]['json']['name'] == "John Smith"
        assert call_args[1]['json']['new_date'] == "2024-01-16"
        assert call_args[1]['json']['new_time'] == "20:00"
        assert call_args[1]['json']['new_party_size'] == 6
        
        assert "✅ Reservation updated successfully" in result
        assert "2024-01-16" in result
        assert "20:00" in result
        print("✅ Successful modification test passed")
    
    # Test partial modification (only time)
    mock_response = MockResponse(200, {
        'name': 'John Smith',
        'phone_number': '+6591234567',
        'reservation_date': '2024-01-15',
        'reservation_time': '20:30',
        'party_size': 4
    })
    
    with patch('realtime_tools.reservation.get_api_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.put.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        result = await _modify_reservation_async(
            phone="91234567",
            name="John Smith",
            new_time="20:30"
        )
        
        # Verify only time was sent
        call_args = mock_client.put.call_args
        assert call_args[1]['json']['name'] == "John Smith"
        assert call_args[1]['json']['new_time'] == "20:30"
        assert 'new_date' not in call_args[1]['json']
        assert 'new_party_size' not in call_args[1]['json']
        
        assert "20:30" in result
        print("✅ Partial modification test passed")
    
    # Test failed modification (wrong credentials)
    mock_response = MockResponse(404)
    
    with patch('realtime_tools.reservation.get_api_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.put.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        result = await _modify_reservation_async(
            phone="91234567",
            name="Wrong Name",
            new_time="20:00"
        )
        
        assert "couldn't find a reservation with those details" in result
        print("✅ Failed modification test passed")
    
    # Test no changes specified
    result = await _modify_reservation_async(
        phone="91234567",
        name="John Smith",
        new_date=None,
        new_time=None,
        new_party_size=None,
        new_special_requests=None
    )
    
    assert "No changes were specified" in result
    print("✅ No changes test passed")


async def test_phone_formatting():
    """Test phone number formatting for Singapore"""
    print("\n=== Testing Phone Number Formatting ===")
    
    test_cases = [
        ("91234567", "+6591234567"),      # 8-digit local
        ("81234567", "+6581234567"),      # 8-digit local
        ("+6591234567", "+6591234567"),   # Already formatted
        ("+14155551234", "+14155551234"), # International
    ]
    
    for input_phone, expected in test_cases:
        # Test in delete operation
        mock_response = MockResponse(200)
        
        with patch('realtime_tools.reservation.get_api_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.delete.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            await _delete_reservation_async(input_phone, "Test Name")
            
            # Check the formatted phone was used
            call_args = mock_client.delete.call_args
            assert expected in call_args[0][0]
            print(f"✅ Format {input_phone} -> {expected} passed")


async def test_error_handling():
    """Test various error scenarios"""
    print("\n=== Testing Error Handling ===")
    
    import httpx
    
    # Test timeout error
    with patch('realtime_tools.reservation.get_api_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.delete.side_effect = httpx.TimeoutException("Timeout")
        mock_get_client.return_value = mock_client
        
        result = await _delete_reservation_async("91234567", "John Smith")
        assert "taking too long to respond" in result
        print("✅ Timeout error test passed")
    
    # Test connection error
    with patch('realtime_tools.reservation.get_api_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.put.side_effect = httpx.RequestError("Connection failed")
        mock_get_client.return_value = mock_client
        
        result = await _modify_reservation_async("91234567", "John Smith", new_time="20:00")
        assert "trouble connecting" in result
        print("✅ Connection error test passed")
    
    # Test unexpected error
    with patch('realtime_tools.reservation.get_api_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.delete.side_effect = Exception("Unexpected error")
        mock_get_client.return_value = mock_client
        
        result = await _delete_reservation_async("91234567", "John Smith")
        assert "Something went wrong" in result
        print("✅ Unexpected error test passed")


async def test_check_availability():
    """Test availability checking"""
    print("\n=== Testing Check Availability ===")
    
    # Test normal party size
    result = check_availability("2024-01-15", "19:00", 4)
    assert "Good news" in result
    assert "availability for 4 people" in result
    print("✅ Normal availability test passed")
    
    # Test large party
    result = check_availability("2024-01-15", "19:00", 10)
    assert "only accommodate parties of up to 8" in result
    print("✅ Large party test passed")


async def run_all_tests():
    """Run all async tests"""
    print("\n" + "="*70)
    print("RESERVATION TOOLS SECURITY TEST SUITE")
    print("Testing secure delete/modify with name verification")
    print("="*70)
    
    try:
        await test_lookup_reservation()
        await test_delete_reservation()
        await test_modify_reservation()
        await test_phone_formatting()
        await test_error_handling()
        await test_check_availability()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        print("\nThe reservation tools are working correctly with:")
        print("- Name verification for delete/modify operations")
        print("- Generic error messages to prevent information leakage")
        print("- Proper phone number formatting")
        print("- Comprehensive error handling")
        
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