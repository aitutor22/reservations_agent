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
from typing import Optional
from agents import function_tool
from .api_client import format_phone_number  # Still need format_phone_number utility

# Import database directly for synchronous access
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from models.db_models import Reservation
from config import config


# DEPRECATED: No longer needed since we use direct database access
# def run_async_from_sync(coro):
#     """
#     Run an async function from a sync context, handling existing event loops.
#     
#     This helper function detects if we're already in an async context (event loop running)
#     and adapts accordingly:
#     - If no event loop is running: uses asyncio.run() normally
#     - If event loop is already running: uses ThreadPoolExecutor to run in a separate thread
#     
#     This is necessary because RealtimeAgent runs in an async context, but @function_tool
#     requires synchronous functions.
#     """
#     import time
#     start_time = time.time()
#     
#     try:
#         # Try to get the running loop
#         loop = asyncio.get_running_loop()
#         print(f"[DEBUG] Running loop detected, using ThreadPoolExecutor")
#     except RuntimeError:
#         # No running loop - we're in a regular sync context
#         # Safe to use asyncio.run()
#         print(f"[DEBUG] No running loop, using asyncio.run()")
#         result = asyncio.run(coro)
#         print(f"[DEBUG] asyncio.run() completed in {time.time() - start_time:.2f}s")
#         return result
#     else:
#         # Already in async context - event loop is running
#         # Can't use asyncio.run(), so run in a separate thread
#         print(f"[DEBUG] Starting ThreadPoolExecutor...")
#         with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
#             print(f"[DEBUG] Submitting coroutine to thread pool...")
#             future = pool.submit(asyncio.run, coro)
#             print(f"[DEBUG] Waiting for future.result()...")
#             result = future.result(timeout=10)  # Add explicit timeout
#             print(f"[DEBUG] ThreadPoolExecutor completed in {time.time() - start_time:.2f}s")
#             return result


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


# DEPRECATED: The async implementations have been removed.
# HTTP calls via httpx timeout in RealtimeAgent context due to event loop issues.
# All reservation tools now use direct database access via SQLAlchemy.
# See the module docstring for details on why this approach was necessary.


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
    """
    # Format phone number for Singapore
    formatted_phone = format_phone_number(phone)
    
    # Use direct database access instead of HTTP
    try:
        # Create a sync database connection
        engine = create_engine(config.SYNC_DATABASE_URL)
        
        with Session(engine) as session:
            # Create new reservation
            reservation = Reservation(
                phone_number=formatted_phone,
                name=name,
                reservation_date=date,
                reservation_time=time,
                party_size=party_size
            )
            
            # Add special requests to other_info if provided
            if special_requests:
                reservation.other_info = {
                    "special_requests": special_requests
                }
            
            # Add to session and commit
            session.add(reservation)
            session.commit()
            
            # Use phone number as confirmation reference
            response_text = f"""✅ Reservation confirmed!
            
Confirmation Reference: {formatted_phone}
Name: {name}
Date: {date}
Time: {time}
Party Size: {party_size}"""
            
            if special_requests:
                response_text += f"\nSpecial Requests: {special_requests}"
            
            response_text += "\n\nWe've recorded your reservation. See you soon at Sakura Ramen House!"
            
            return response_text
            
    except Exception as e:
        print(f"[ERROR] Database error in make_reservation: {e}")
        return "I'm having trouble making the reservation. Please try again in a moment."



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
                # Verify the name matches (case-insensitive for better UX)
                if reservation.name.lower() == name.lower():
                    # Delete the reservation
                    session.delete(reservation)
                    session.commit()
                    return f"✅ Your reservation has been cancelled successfully. We hope to see you another time!"
                else:
                    # Name doesn't match - don't reveal if reservation exists
                    return "I couldn't find a reservation with those details. Please check your name and phone number."
            else:
                # No reservation found
                return "I couldn't find a reservation with those details. Please check your name and phone number."
                
    except Exception as e:
        print(f"[ERROR] Database error in delete_reservation: {e}")
        return "I'm having trouble cancelling your reservation. Please try again in a moment."


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
    # Format phone number for Singapore
    formatted_phone = format_phone_number(phone)
    
    # Check if any changes were specified
    changes = []
    if new_date:
        changes.append(f"Date: {new_date}")
    if new_time:
        changes.append(f"Time: {new_time}")
    if new_party_size is not None:
        changes.append(f"Party size: {new_party_size}")
    if new_special_requests is not None:
        changes.append(f"Special requests: {new_special_requests}")
    
    if not changes:
        return "No changes were specified. Please tell me what you'd like to modify."
    
    # Use direct database access instead of HTTP
    try:
        # Create a sync database connection
        engine = create_engine(config.SYNC_DATABASE_URL)
        
        with Session(engine) as session:
            # Query for the reservation
            stmt = select(Reservation).where(Reservation.phone_number == formatted_phone)
            reservation = session.execute(stmt).scalar_one_or_none()
            
            if reservation:
                # Verify the name matches (case-insensitive for better UX)
                if reservation.name.lower() == name.lower():
                    # Update the reservation fields
                    if new_date:
                        reservation.reservation_date = new_date
                    if new_time:
                        reservation.reservation_time = new_time
                    if new_party_size is not None:
                        reservation.party_size = new_party_size
                    if new_special_requests is not None:
                        # Update or create other_info
                        if reservation.other_info is None:
                            reservation.other_info = {}
                        reservation.other_info["special_requests"] = new_special_requests
                    
                    # Commit the changes
                    session.commit()
                    
                    # Build response with updated details
                    response_text = f"""✅ Reservation updated successfully!

Updated Details:
Name: {reservation.name}
Phone: {reservation.phone_number}
Date: {reservation.reservation_date}
Time: {reservation.reservation_time}
Party Size: {reservation.party_size}"""
                    
                    if reservation.other_info and reservation.other_info.get('special_requests'):
                        response_text += f"\nSpecial Requests: {reservation.other_info['special_requests']}"
                    
                    response_text += "\n\nWe look forward to seeing you!"
                    
                    return response_text
                else:
                    # Name doesn't match - don't reveal if reservation exists
                    return "I couldn't find a reservation with those details. Please check your name and phone number."
            else:
                # No reservation found
                return "I couldn't find a reservation with those details. Please check your name and phone number."
                
    except Exception as e:
        print(f"[ERROR] Database error in modify_reservation: {e}")
        return "I'm having trouble updating your reservation. Please try again in a moment."

