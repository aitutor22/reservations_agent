"""
Reservation Management Tools
Tools for checking availability and creating reservations

ARCHITECTURE NOTE: Enhanced Sync/Async Bridge Pattern
------------------------------------------------------
This module uses an enhanced "sync wrapper around async implementation" pattern:

1. @function_tool decorated functions MUST be synchronous (limitation of the decorator)
2. Our API calls use httpx which REQUIRES async/await for non-blocking operations
3. RealtimeAgent runs in an async context with an event loop already running
4. Solution: Detect if there's a running loop and handle accordingly:
   - If no loop: use asyncio.run() (standard sync context)
   - If loop exists: use ThreadPoolExecutor to run in separate thread

Example:
    @function_tool
    def tool_function(...):  # Sync function for the agent
        return run_async_from_sync(_async_implementation(...))
    
    async def _async_implementation(...):  # Async function for API calls
        response = await httpx_client.post(...)

This ensures the voice agent doesn't experience audio stuttering from blocked I/O
and works correctly whether called from sync or async context.
"""
import asyncio
import concurrent.futures
import httpx
from agents import function_tool
from .api_client import get_api_client, format_phone_number


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
    try:
        # Try to get the running loop
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop - we're in a regular sync context
        # Safe to use asyncio.run()
        return asyncio.run(coro)
    else:
        # Already in async context - event loop is running
        # Can't use asyncio.run(), so run in a separate thread
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()


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
    client = await get_api_client()
    
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