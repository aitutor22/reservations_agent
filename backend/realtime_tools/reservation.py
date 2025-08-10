"""
Reservation Management Tools
Tools for checking availability and creating reservations

ARCHITECTURE NOTE: Direct Database Access Workaround
-----------------------------------------------------
This module currently uses DIRECT DATABASE ACCESS instead of HTTP API calls.

## The Issue:
When function_tool decorated functions are executed within the RealtimeAgent's async context,
ALL network requests (httpx, requests, even subprocess curl) timeout. This appears to be due to
complex event loop interactions when the RealtimeAgent executes synchronous function_tools that
try to make async HTTP calls within ThreadPoolExecutor contexts.

## Current Solution:
We bypass the HTTP API entirely and query the PostgreSQL database directly using SQLAlchemy's
synchronous interface. This avoids all network calls and event loop complications.

## Why This Works:
- Direct database queries use psycopg2's synchronous interface (no event loop issues)
- The database is in the same process as the API (no network latency)
- Queries are fast enough to not cause audio stuttering

## KIV (Keep In View) - Future Improvements:
1. Investigate why HTTP requests timeout in the RealtimeAgent context
2. Consider using a message queue or Redis for communication
3. Explore if newer versions of the agents SDK resolve this issue
4. Test with different async HTTP libraries (aiohttp, urllib3)

Note: This is not ideal architecture as it couples the tools directly to the database,
but it's a pragmatic solution that ensures the voice agent works reliably.

Original async/HTTP pattern preserved below for reference and future migration.
"""
import asyncio
import concurrent.futures
import httpx
from typing import Optional
from agents import function_tool
from .api_client import get_api_client, format_phone_number

# Import database directly for synchronous access
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from models.db_models import Reservation
from config import config
import json


def run_async_from_sync(coro):
    """
    Run an async function from a sync context, handling existing event loops.
    
    This helper function detects if we're already in an async context (event loop running)
    and adapts accordingly:
    - If no event loop is running: uses asyncio.run() normally
    - If event loop is already running: uses ThreadPoolExecutor to run in a separate thread
    
    This is necessary because RealtimeAgent runs in an async context, but @function_tool
    requires synchronous functions.
    """
    import time
    start_time = time.time()
    
    try:
        # Try to get the running loop
        loop = asyncio.get_running_loop()
        print(f"[DEBUG] Running loop detected, using ThreadPoolExecutor")
    except RuntimeError:
        # No running loop - we're in a regular sync context
        # Safe to use asyncio.run()
        print(f"[DEBUG] No running loop, using asyncio.run()")
        result = asyncio.run(coro)
        print(f"[DEBUG] asyncio.run() completed in {time.time() - start_time:.2f}s")
        return result
    else:
        # Already in async context - event loop is running
        # Can't use asyncio.run(), so run in a separate thread
        print(f"[DEBUG] Starting ThreadPoolExecutor...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            print(f"[DEBUG] Submitting coroutine to thread pool...")
            future = pool.submit(asyncio.run, coro)
            print(f"[DEBUG] Waiting for future.result()...")
            result = future.result(timeout=10)  # Add explicit timeout
            print(f"[DEBUG] ThreadPoolExecutor completed in {time.time() - start_time:.2f}s")
            return result


@function_tool
def lookup_reservation(phone: str) -> str:
    """
    Look up an existing reservation by phone number.
    
    Args:
        phone: Contact phone number (will be auto-formatted for Singapore if 8 digits)
    
    Returns:
        Reservation details if found, or a not found message
    """
    # Format phone number for Singapore
    formatted_phone = format_phone_number(phone)
    
    # Use direct database access instead of HTTP
    try:
        # Create a sync database connection
        engine = create_engine(config.SYNC_DATABASE_URL)
        
        with Session(engine) as session:
            # Query for the reservation
            stmt = select(Reservation).where(Reservation.phone_number == formatted_phone)
            reservation = session.execute(stmt).scalar_one_or_none()
            
            if reservation:
                
                # Format the response
                response_text = f"""✅ Reservation found!

Name: {reservation.name}
Phone: {reservation.phone_number}
Date: {reservation.reservation_date}
Time: {reservation.reservation_time}
Party Size: {reservation.party_size}"""
                
                # Add special requests if present
                if reservation.other_info and isinstance(reservation.other_info, dict):
                    special_requests = reservation.other_info.get('special_requests')
                    if special_requests:
                        response_text += f"\nSpecial Requests: {special_requests}"
                
                return response_text
            else:
                return f"No reservation found for phone number {formatted_phone}. Would you like to make a new reservation?"
                
    except Exception as e:
        print(f"[ERROR] Database error in lookup_reservation: {e}")
        return "I'm having trouble accessing our reservation system. Please try again in a moment."


async def _lookup_reservation_async(phone: str) -> str:
    """
    Async implementation to look up a reservation by phone number.
    """
    import time
    start_time = time.time()
    print(f"[DEBUG] _lookup_reservation_async called with phone: {phone}")
    
    # Format phone number for Singapore
    formatted_phone = format_phone_number(phone)
    print(f"[DEBUG] Formatted phone: {formatted_phone}")
    
    # Create a new client for each call to avoid event loop issues
    print(f"[DEBUG] Creating httpx.AsyncClient...")
    try:
        # Try with explicit headers and longer timeout
        # Use 127.0.0.1 instead of localhost to avoid potential DNS issues
        async with httpx.AsyncClient(
            base_url="http://127.0.0.1:8000",
            timeout=httpx.Timeout(30.0, connect=5.0),
            headers={"Accept": "application/json"}
        ) as client:
            print(f"[DEBUG] Client created with base_url=http://127.0.0.1:8000")
            print(f"[DEBUG] Making API call to /api/reservations/{formatted_phone}")
            print(f"[DEBUG] Time elapsed: {time.time() - start_time:.2f}s")
            
            response = await client.get(
                f"/api/reservations/{formatted_phone}",
                headers={"Connection": "close"}  # Disable keep-alive
            )
            print(f"[DEBUG] API response status: {response.status_code}")
            print(f"[DEBUG] Total time elapsed: {time.time() - start_time:.2f}s")
            
            if response.status_code == 200:
                data = response.json()
                
                # Format the reservation details nicely
                response_text = f"""✅ Reservation found!

Name: {data.get('name')}
Phone: {data.get('phone_number')}
Date: {data.get('reservation_date')}
Time: {data.get('reservation_time')}
Party Size: {data.get('party_size')}"""
                
                other_info = data.get('other_info', {})
                if other_info and other_info.get('special_requests'):
                    response_text += f"\nSpecial Requests: {other_info['special_requests']}"
                
                print(f"[DEBUG] Returning success response with reservation details")
                return response_text
                
            elif response.status_code == 404:
                print(f"[DEBUG] No reservation found (404)")
                return f"No reservation found for phone number {formatted_phone}. Would you like to make a new reservation?"
                
            else:
                print(f"[DEBUG] Unexpected status code: {response.status_code}")
                return "I'm having trouble looking up your reservation. Please try again or provide more details."
                
    except httpx.TimeoutException as e:
        print(f"[DEBUG] httpx.TimeoutException caught: {e}")
        print(f"[DEBUG] Exception type: {type(e)}")
        print(f"[DEBUG] Time elapsed before timeout: {time.time() - start_time:.2f}s")
        return "The system is taking too long to respond. Please try again."
        
    except httpx.RequestError as e:
        print(f"[DEBUG] httpx.RequestError caught: {e}")
        print(f"[DEBUG] Exception type: {type(e)}")
        print(f"[DEBUG] Time elapsed before error: {time.time() - start_time:.2f}s")
        return "I'm having trouble connecting to our reservation system. Please try again in a moment."
        
    except Exception as e:
        print(f"[DEBUG] Unexpected exception caught: {e}")
        print(f"[DEBUG] Exception type: {type(e)}")
        print(f"[DEBUG] Time elapsed before error: {time.time() - start_time:.2f}s")
        import traceback
        traceback.print_exc()
        return "Something went wrong while looking up your reservation. Please try again."


@function_tool
def check_availability(date: str, time: str, party_size: int) -> str:
    """
    Check if a reservation slot is available. Always call this before confirming any reservation.
    
    Args:
        date: Date in format YYYY-MM-DD
        time: Time in format HH:MM
        party_size: Number of people
    """
    # For demo, always return available (no random failures)
    if party_size > 8:
        return "I'm sorry, but we can only accommodate parties of up to 8 people. For larger groups, please call us directly."
    
    # Always available for demo
    return f"Good news! We have availability for {party_size} people on {date} at {time}. Would you like me to make a reservation?"


@function_tool
def make_reservation(name: str, phone: str, date: str, time: str, party_size: int, special_requests: str = "") -> str:
    """
    Create a reservation. Only call this after checking availability and collecting all required information.
    
    Args:
        name: Guest name
        phone: Contact phone number
        date: Date in format YYYY-MM-DD
        time: Time in format HH:MM
        party_size: Number of people
        special_requests: Any special requests or dietary restrictions
    
    Note: This is a synchronous wrapper function because @function_tool doesn't support async.
    It uses run_async_from_sync() to handle both sync and async contexts.
    """
    # IMPORTANT: Enhanced sync/async bridge pattern:
    # 1. The @function_tool decorator only supports synchronous functions
    # 2. httpx (our HTTP client) requires async/await for non-blocking API calls
    # 3. RealtimeAgent runs in async context, so we can't always use asyncio.run()
    # 4. run_async_from_sync() detects the context and adapts accordingly
    return run_async_from_sync(_make_reservation_async(name, phone, date, time, party_size, special_requests))


async def _make_reservation_async(name: str, phone: str, date: str, time: str, party_size: int, special_requests: str = "") -> str:
    """
    Async implementation that performs the actual API call.
    
    This function:
    1. Uses httpx's async client (non-blocking, won't cause audio stuttering)
    2. Formats phone numbers for Singapore (+65 prefix)
    3. Calls the POST /api/reservations endpoint
    4. Handles various error cases with user-friendly messages
    
    We need this separate async function because:
    - httpx.AsyncClient requires await for all operations
    - Using the sync requests library would block the event loop
    - Blocking would cause audio interruptions in the voice agent
    """
    
    # Format phone number for Singapore
    formatted_phone = format_phone_number(phone)
    
    # Prepare reservation data
    reservation_data = {
        "phone_number": formatted_phone,
        "name": name,
        "reservation_date": date,
        "reservation_time": time,
        "party_size": party_size
    }
    
    # Add special requests to other_info if provided
    if special_requests:
        reservation_data["other_info"] = {
            "special_requests": special_requests
        }
    
    # Create a new client for each call to avoid event loop issues
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        try:
            response = await client.post(
                "/api/reservations",
                json=reservation_data,
                timeout=10.0  # Shorter timeout for better UX
            )
            
            if response.status_code == 200:
                data = response.json()
                # Use phone number as confirmation reference
                confirmation_ref = data.get('phone_number', formatted_phone)
                
                response_text = f"""✅ Reservation confirmed!
                
Confirmation Reference: {confirmation_ref}
Name: {name}
Date: {date}
Time: {time}
Party Size: {party_size}"""
                
                if special_requests:
                    response_text += f"\nSpecial Requests: {special_requests}"
                
                response_text += "\n\nWe've recorded your reservation. See you soon at Sakura Ramen House!"
                
                return response_text
                
            elif response.status_code == 400:
                # Validation error - extract detail
                error_detail = response.json().get('detail', 'Invalid reservation data')
                
                # Provide helpful message for phone number errors
                if 'phone' in error_detail.lower():
                    return f"I need a valid phone number to complete the reservation. Please provide an 8-digit Singapore number (like 91234567) or an international number starting with + (like +6591234567)."
                
                return f"I couldn't make that reservation: {error_detail}"
                
            elif response.status_code == 500:
                return "I'm having trouble with our reservation system. Please try again in a moment."
                
            else:
                return "I couldn't complete the reservation. Please try again or call us directly."
                
        except httpx.TimeoutException:
            return "The reservation system is taking too long to respond. Please try again."
            
        except httpx.RequestError as e:
            print(f"API connection error: {e}")
            return "I'm having trouble connecting to our reservation system. Please try again in a moment."
            
        except Exception as e:
            print(f"Unexpected error in make_reservation: {e}")
            return "Something went wrong while making the reservation. Please try again or call us directly."


@function_tool
def delete_reservation(phone: str, name: str) -> str:
    """
    Cancel/delete a reservation after verifying ownership.
    
    Args:
        phone: Contact phone number (will be auto-formatted for Singapore if 8 digits)
        name: Name on the reservation (for verification)
    
    Returns:
        Success or failure message
    """
    return run_async_from_sync(_delete_reservation_async(phone, name))


async def _delete_reservation_async(phone: str, name: str) -> str:
    """
    Async implementation to delete a reservation with verification.
    """
    # Format phone number for Singapore
    formatted_phone = format_phone_number(phone)
    
    # Create a new client for each call to avoid event loop issues
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        try:
            import json as json_lib
            response = await client.delete(
                f"/api/reservations/{formatted_phone}",
                content=json_lib.dumps({"name": name}),
                headers={"Content-Type": "application/json"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                return f"✅ Your reservation has been cancelled successfully. We hope to see you another time!"
                
            elif response.status_code == 404:
                # Generic message to not reveal if reservation exists
                return "I couldn't find a reservation with those details. Please check your name and phone number."
                
            else:
                return "I'm having trouble cancelling your reservation. Please try again."
                
        except httpx.TimeoutException:
            return "The system is taking too long to respond. Please try again."
            
        except httpx.RequestError as e:
            print(f"API connection error: {e}")
            return "I'm having trouble connecting to our reservation system. Please try again in a moment."
            
        except Exception as e:
            print(f"Unexpected error in delete_reservation: {e}")
            return "Something went wrong while cancelling your reservation. Please try again."


@function_tool
def modify_reservation(
    phone: str, 
    name: str,
    new_date: Optional[str] = None,
    new_time: Optional[str] = None,
    new_party_size: Optional[int] = None,
    new_special_requests: Optional[str] = None
) -> str:
    """
    Modify an existing reservation after verifying ownership.
    
    Args:
        phone: Contact phone number (will be auto-formatted for Singapore if 8 digits)
        name: Name on the reservation (for verification)
        new_date: New date in YYYY-MM-DD format (optional)
        new_time: New time in HH:MM format (optional)
        new_party_size: New number of guests (optional)
        new_special_requests: New special requests or dietary restrictions (optional)
    
    Returns:
        Updated reservation details or error message
    """
    return run_async_from_sync(_modify_reservation_async(
        phone, name, new_date, new_time, new_party_size, new_special_requests
    ))


async def _modify_reservation_async(
    phone: str,
    name: str,
    new_date: Optional[str],
    new_time: Optional[str],
    new_party_size: Optional[int],
    new_special_requests: Optional[str]
) -> str:
    """
    Async implementation to modify a reservation with verification.
    """
    # Format phone number for Singapore
    formatted_phone = format_phone_number(phone)
    
    # Build update request
    update_data = {"name": name}
    changes = []
    
    if new_date:
        update_data["new_date"] = new_date
        changes.append(f"Date: {new_date}")
    if new_time:
        update_data["new_time"] = new_time
        changes.append(f"Time: {new_time}")
    if new_party_size is not None:
        update_data["new_party_size"] = new_party_size
        changes.append(f"Party size: {new_party_size}")
    if new_special_requests is not None:
        update_data["new_special_requests"] = new_special_requests
        changes.append(f"Special requests: {new_special_requests}")
    
    if not changes:
        return "No changes were specified. Please tell me what you'd like to modify."
    
    # Create a new client for each call to avoid event loop issues
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        try:
            response = await client.put(
                f"/api/reservations/{formatted_phone}",
                json=update_data,
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                
                response_text = f"""✅ Reservation updated successfully!

Updated Details:
Name: {data.get('name')}
Phone: {data.get('phone_number')}
Date: {data.get('reservation_date')}
Time: {data.get('reservation_time')}
Party Size: {data.get('party_size')}"""
                
                other_info = data.get('other_info', {})
                if other_info and other_info.get('special_requests'):
                    response_text += f"\nSpecial Requests: {other_info['special_requests']}"
                
                response_text += "\n\nWe look forward to seeing you!"
                
                return response_text
                
            elif response.status_code == 404:
                # Generic message to not reveal if reservation exists
                return "I couldn't find a reservation with those details. Please check your name and phone number."
                
            elif response.status_code == 400:
                error_detail = response.json().get('detail', 'Invalid update data')
                return f"I couldn't update your reservation: {error_detail}"
                
            else:
                return "I'm having trouble updating your reservation. Please try again."
                
        except httpx.TimeoutException:
            return "The system is taking too long to respond. Please try again."
            
        except httpx.RequestError as e:
            print(f"API connection error: {e}")
            return "I'm having trouble connecting to our reservation system. Please try again in a moment."
            
        except Exception as e:
            print(f"Unexpected error in modify_reservation: {e}")
            return "Something went wrong while updating your reservation. Please try again."