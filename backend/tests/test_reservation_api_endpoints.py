#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for reservation API endpoints with security features
Tests DELETE and PUT endpoints with name verification
"""

import sys
import os
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from main import app


# Create test client
client = TestClient(app)


def test_delete_reservation_success():
    """Test successful reservation deletion with correct credentials"""
    print("\n=== Testing DELETE /api/reservations/{phone} ===")
    
    with patch('api.routes.reservations.get_reservation_service') as mock_get_service:
        mock_service = AsyncMock()
        mock_service.delete_reservation.return_value = True
        mock_get_service.return_value = mock_service
        
        response = client.delete(
            "/api/reservations/+6591234567",
            json={"name": "John Smith"}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Reservation cancelled successfully"
        
        # Verify service was called with both parameters
        mock_service.delete_reservation.assert_called_once_with(
            "+6591234567", "John Smith"
        )
        print("✅ Successful deletion test passed")


def test_delete_reservation_not_found():
    """Test deletion with wrong credentials returns generic error"""
    print("\n=== Testing DELETE with wrong credentials ===")
    
    with patch('api.routes.reservations.get_reservation_service') as mock_get_service:
        mock_service = AsyncMock()
        mock_service.delete_reservation.return_value = False  # Verification failed
        mock_get_service.return_value = mock_service
        
        response = client.delete(
            "/api/reservations/+6591234567",
            json={"name": "Wrong Name"}
        )
        
        assert response.status_code == 404
        assert response.json()["detail"] == "No reservation found with those details"
        print("✅ Wrong credentials test passed")


def test_update_reservation_success():
    """Test successful reservation update with correct credentials"""
    print("\n=== Testing PUT /api/reservations/{phone} ===")
    
    from models.reservation import ReservationResponse
    
    mock_updated = {
        'id': 1,
        'name': 'John Smith',
        'phone_number': '+6591234567',
        'reservation_date': '2024-01-16',
        'reservation_time': '20:00',
        'party_size': 6,
        'other_info': {'special_requests': 'Birthday'}
    }
    
    with patch('api.routes.reservations.get_reservation_service') as mock_get_service:
        mock_service = AsyncMock()
        mock_service.update_reservation.return_value = ReservationResponse(**mock_updated)
        mock_get_service.return_value = mock_service
        
        response = client.put(
            "/api/reservations/+6591234567",
            json={
                "name": "John Smith",
                "new_date": "2024-01-16",
                "new_time": "20:00",
                "new_party_size": 6,
                "new_special_requests": "Birthday"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["reservation_date"] == "2024-01-16"
        assert data["reservation_time"] == "20:00"
        assert data["party_size"] == 6
        print("✅ Successful update test passed")


def test_update_reservation_partial():
    """Test partial update (only some fields)"""
    print("\n=== Testing partial update ===")
    
    from models.reservation import ReservationResponse
    
    mock_updated = {
        'id': 1,
        'name': 'John Smith',
        'phone_number': '+6591234567',
        'reservation_date': '2024-01-15',  # Unchanged
        'reservation_time': '20:30',       # Changed
        'party_size': 4                    # Unchanged
    }
    
    with patch('api.routes.reservations.get_reservation_service') as mock_get_service:
        mock_service = AsyncMock()
        mock_service.update_reservation.return_value = ReservationResponse(**mock_updated)
        mock_get_service.return_value = mock_service
        
        response = client.put(
            "/api/reservations/+6591234567",
            json={
                "name": "John Smith",
                "new_time": "20:30"  # Only updating time
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["reservation_time"] == "20:30"
        
        # Verify service was called with correct update data
        call_args = mock_service.update_reservation.call_args
        assert call_args[0][0] == "+6591234567"
        assert call_args[0][1] == "John Smith"
        update_obj = call_args[0][2]
        assert update_obj.reservation_time == "20:30"
        print("✅ Partial update test passed")


def test_update_reservation_not_found():
    """Test update with wrong credentials returns generic error"""
    print("\n=== Testing PUT with wrong credentials ===")
    
    with patch('api.routes.reservations.get_reservation_service') as mock_get_service:
        mock_service = AsyncMock()
        mock_service.update_reservation.return_value = None  # Verification failed
        mock_get_service.return_value = mock_service
        
        response = client.put(
            "/api/reservations/+6591234567",
            json={
                "name": "Wrong Name",
                "new_time": "20:00"
            }
        )
        
        assert response.status_code == 404
        assert response.json()["detail"] == "No reservation found with those details"
        print("✅ Wrong credentials update test passed")


def test_update_reservation_no_fields():
    """Test update with no fields to update"""
    print("\n=== Testing PUT with no update fields ===")
    
    response = client.put(
        "/api/reservations/+6591234567",
        json={
            "name": "John Smith"
            # No update fields provided
        }
    )
    
    assert response.status_code == 400
    assert response.json()["detail"] == "No fields to update provided"
    print("✅ No fields error test passed")


def test_create_reservation():
    """Test reservation creation endpoint"""
    print("\n=== Testing POST /api/reservations ===")
    
    from models.reservation import ReservationResponse
    
    mock_created = {
        'id': 1,
        'name': 'John Smith',
        'phone_number': '+6591234567',
        'reservation_date': '2024-01-15',
        'reservation_time': '19:00',
        'party_size': 4
    }
    
    with patch('api.routes.reservations.get_reservation_service') as mock_get_service:
        mock_service = AsyncMock()
        mock_service.create_reservation.return_value = ReservationResponse(**mock_created)
        mock_get_service.return_value = mock_service
        
        response = client.post(
            "/api/reservations",
            json={
                "name": "John Smith",
                "phone_number": "+6591234567",
                "reservation_date": "2024-01-15",
                "reservation_time": "19:00",
                "party_size": 4
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "John Smith"
        assert data["phone_number"] == "+6591234567"
        print("✅ Create reservation test passed")


def test_get_reservation():
    """Test reservation lookup endpoint"""
    print("\n=== Testing GET /api/reservations/{phone} ===")
    
    from models.reservation import ReservationResponse
    
    mock_reservation = {
        'id': 1,
        'name': 'John Smith',
        'phone_number': '+6591234567',
        'reservation_date': '2024-01-15',
        'reservation_time': '19:00',
        'party_size': 4,
        'other_info': {'special_requests': 'Window seat'}
    }
    
    with patch('api.routes.reservations.get_reservation_service') as mock_get_service:
        mock_service = AsyncMock()
        mock_service.get_reservation_by_phone.return_value = ReservationResponse(**mock_reservation)
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/reservations/+6591234567")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "John Smith"
        assert data["other_info"]["special_requests"] == "Window seat"
        print("✅ Get reservation test passed")


def test_get_reservation_not_found():
    """Test lookup for non-existent reservation"""
    print("\n=== Testing GET for non-existent reservation ===")
    
    with patch('api.routes.reservations.get_reservation_service') as mock_get_service:
        mock_service = AsyncMock()
        mock_service.get_reservation_by_phone.return_value = None
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/reservations/+6599999999")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Reservation not found"
        print("✅ Not found test passed")


def test_api_error_handling():
    """Test API error handling"""
    print("\n=== Testing API Error Handling ===")
    
    # Test create with invalid data
    with patch('api.routes.reservations.get_reservation_service') as mock_get_service:
        mock_service = AsyncMock()
        mock_service.create_reservation.side_effect = ValueError("Invalid phone number")
        mock_get_service.return_value = mock_service
        
        response = client.post(
            "/api/reservations",
            json={
                "name": "John Smith",
                "phone_number": "invalid",
                "reservation_date": "2024-01-15",
                "reservation_time": "19:00",
                "party_size": 4
            }
        )
        
        assert response.status_code == 400
        assert "Invalid phone number" in response.json()["detail"]
        print("✅ Validation error test passed")
    
    # Test server error
    with patch('api.routes.reservations.get_reservation_service') as mock_get_service:
        mock_service = AsyncMock()
        mock_service.create_reservation.side_effect = Exception("Database error")
        mock_get_service.return_value = mock_service
        
        response = client.post(
            "/api/reservations",
            json={
                "name": "John Smith",
                "phone_number": "+6591234567",
                "reservation_date": "2024-01-15",
                "reservation_time": "19:00",
                "party_size": 4
            }
        )
        
        assert response.status_code == 500
        assert "Failed to create reservation" in response.json()["detail"]
        print("✅ Server error test passed")


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("RESERVATION API SECURITY TEST SUITE")
    print("Testing DELETE and PUT endpoints with name verification")
    print("="*70)
    
    try:
        # Test DELETE endpoint
        test_delete_reservation_success()
        test_delete_reservation_not_found()
        
        # Test PUT endpoint
        test_update_reservation_success()
        test_update_reservation_partial()
        test_update_reservation_not_found()
        test_update_reservation_no_fields()
        
        # Test other endpoints
        test_create_reservation()
        test_get_reservation()
        test_get_reservation_not_found()
        
        # Test error handling
        test_api_error_handling()
        
        print("\n" + "="*70)
        print("✅ ALL API TESTS PASSED!")
        print("="*70)
        print("\nThe API endpoints are working correctly with:")
        print("- Name verification for DELETE and PUT operations")
        print("- Generic error messages for security")
        print("- Partial update support")
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


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)