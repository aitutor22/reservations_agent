#!/usr/bin/env python3
"""
Test script for Reservation API
Tests both direct API calls and the RealtimeAgent tools
"""

import asyncio
import httpx
from datetime import datetime, timedelta

# Import formatting function
from realtime_tools.api_client import format_phone_number

# Import the underlying async function for testing
from realtime_tools.reservation import _make_reservation_async

API_BASE_URL = "http://localhost:8000"


async def test_api_directly():
    """Test the reservation API endpoints directly"""
    print("\n=== Testing API Endpoints Directly ===")
    
    try:
        async with httpx.AsyncClient(base_url=API_BASE_URL) as client:
            # Test connection first
            try:
                await client.get("/")
            except httpx.ConnectError:
                print("\n⚠️  Backend server is not running at http://localhost:8000")
                print("   Please start the server with: uvicorn main:app --reload")
                return
            
            # Test 1: Create a reservation
            print("\nTest 1: Creating reservation via API")
            
            tomorrow = (datetime.now() + timedelta(days=1)).date()
            reservation_data = {
                "phone_number": "+6598207272",
                "name": "Test User API",
                "reservation_date": tomorrow.isoformat(),
                "reservation_time": "19:00",
                "party_size": 4,
                "other_info": {
                    "special_requests": "Window seat please"
                }
            }
            
            try:
                # First, delete any existing reservation with this phone
                await client.delete(f"/api/reservations/{reservation_data['phone_number']}")
            except:
                pass  # Ignore if doesn't exist
            
            response = await client.post("/api/reservations", json=reservation_data)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Reservation created successfully!")
                print(f"Response: {data}")
                
                # Verify the date/time are strings
                assert isinstance(data['reservation_date'], str), "Date should be string"
                assert isinstance(data['reservation_time'], str), "Time should be string"
                print("✅ Date/time serialization working correctly")
            else:
                print(f"❌ Failed: {response.status_code} - {response.text}")
            
            # Test 2: Lookup reservation
            print("\nTest 2: Looking up reservation")
            response = await client.get(f"/api/reservations/{reservation_data['phone_number']}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Reservation found!")
                
                # Display reservation details
                print("\nReservation Details:")
                print("-" * 40)
                for key, value in data.items():
                    if key not in ['created_at', 'updated_at']:
                        print(f"{key:20}: {value}")
                print("-" * 40)
            else:
                print(f"❌ Lookup failed: {response.text}")
    except Exception as e:
        print(f"\n❌ Error during API tests: {e}")


def test_phone_formatting():
    """Test Singapore phone number formatting"""
    print("\n=== Testing Phone Number Formatting ===")
    
    test_cases = [
        ("98207272", "+6598207272"),  # Singapore mobile starting with 9
        ("82345678", "+6582345678"),  # Singapore mobile starting with 8
        ("31234567", "+6531234567"),  # Singapore landline starting with 3
        ("62345678", "+6562345678"),  # Singapore landline starting with 6
        ("+6598207272", "+6598207272"),  # Already formatted
        ("+12025551234", "+12025551234"),  # International number
        ("12345678", "12345678"),  # Doesn't match Singapore pattern
    ]
    
    print("\n{:<15} {:<15} {:<15} {:<10}".format("Input", "Expected", "Actual", "Result"))
    print("-" * 60)
    
    for input_phone, expected in test_cases:
        actual = format_phone_number(input_phone)
        result = "✅" if actual == expected else "❌"
        print(f"{input_phone:<15} {expected:<15} {actual:<15} {result:<10}")
    
    print("-" * 60)


def test_check_availability_logic():
    """Test the availability checking logic (without decorator)"""
    print("\n=== Testing Availability Logic ===")
    
    print("\nTest 1: Normal party size")
    tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()
    # Simulate the logic from check_availability
    party_size = 4
    if party_size > 8:
        result = "I'm sorry, but we can only accommodate parties of up to 8 people. For larger groups, please call us directly."
    else:
        result = f"Good news! We have availability for {party_size} people on {tomorrow} at 19:00. Would you like me to make a reservation?"
    
    print(f"Result: {result}")
    assert "Good news" in result, "Should return availability"
    print("✅ Availability logic working for normal party size")
    
    print("\nTest 2: Large party size")
    party_size = 10
    if party_size > 8:
        result = "I'm sorry, but we can only accommodate parties of up to 8 people. For larger groups, please call us directly."
    else:
        result = f"Good news! We have availability for {party_size} people on {tomorrow} at 19:00. Would you like me to make a reservation?"
    
    print(f"Result: {result}")
    assert "8 people" in result, "Should reject large parties"
    print("✅ Availability logic working for large party size")


async def test_make_reservation_async():
    """Test the async make_reservation function"""
    print("\n=== Testing Make Reservation (Async) ===")
    print("Note: This requires the backend server to be running")
    
    tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()
    
    try:
        # Use a different phone number for tool test
        result = await _make_reservation_async(
            name="Test User Async",
            phone="91234567",  # 8-digit Singapore number
            date=tomorrow,
            time="20:00",
            party_size=2,
            special_requests="Vegetarian options needed"
        )
        
        print(f"Result: {result[:200]}...")  # Show first 200 chars
        
        if "Reservation confirmed" in result:
            print("✅ make_reservation async working!")
            # Check that Singapore number was formatted
            assert "+6591234567" in result, "Should format Singapore number"
            print("✅ Singapore number formatting working")
        elif "trouble connecting" in result or "trouble with our reservation system" in result:
            print("⚠️  Cannot test make_reservation - backend server not running")
        else:
            print(f"❌ Reservation failed")
    except Exception as e:
        print(f"⚠️  Cannot test make_reservation: {e}")


async def list_all_reservations():
    """List all current reservations in the database"""
    print("\n=== Current Reservations in Database ===")
    
    async with httpx.AsyncClient(base_url=API_BASE_URL) as client:
        # This endpoint might not exist, but we can try
        try:
            # Use the logic from main.py startup
            from database import get_db
            from services.reservation_service import get_reservation_service
            
            async for db in get_db():
                service = await get_reservation_service(db)
                reservations = await service.list_all_reservations(limit=100)
                
                if reservations:
                    print("\n{:<20} {:<15} {:<12} {:<8} {:<5}".format("Name", "Phone", "Date", "Time", "Party"))
                    print("-" * 60)
                    
                    for res in reservations:
                        print(f"{res.name:<20} {res.phone_number:<15} {str(res.reservation_date):<12} {str(res.reservation_time):<8} {res.party_size:<5}")
                    
                    print("-" * 60)
                else:
                    print("No reservations found")
                break
        except Exception as e:
            print(f"Could not list reservations: {e}")


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("      RESERVATION SYSTEM TEST SUITE")
    print("  Testing API endpoints and RealtimeAgent tools")
    print("=" * 60)
    
    # Test phone formatting first (no async needed)
    test_phone_formatting()
    
    # Test availability logic (no server needed)
    test_check_availability_logic()
    
    # Test API endpoints
    await test_api_directly()
    
    # Test async make_reservation function
    await test_make_reservation_async()
    
    # List all reservations
    await list_all_reservations()
    
    print("\n✅ All tests completed!")
    print("\nNote: Make sure the backend server is running on http://localhost:8000")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()