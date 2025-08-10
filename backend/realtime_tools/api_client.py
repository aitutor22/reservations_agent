"""
API Client for Realtime Tools
Thread-local httpx clients to avoid cross-event-loop issues
"""
import httpx
import threading
from typing import Optional

# Thread-local storage for clients
# Each thread (including ThreadPoolExecutor threads) gets its own client
_thread_local = threading.local()


async def get_api_client() -> httpx.AsyncClient:
    """
    Get or create a thread-local API client.
    
    This ensures each thread has its own AsyncClient instance,
    avoiding cross-event-loop issues when using ThreadPoolExecutor.
    Connection pooling still works within each thread.
    """
    if not hasattr(_thread_local, 'client') or _thread_local.client is None:
        _thread_local.client = httpx.AsyncClient(
            base_url="http://localhost:8000",
            timeout=30.0,
            limits=httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10
            )
        )
    return _thread_local.client


async def cleanup_api_client():
    """
    Cleanup the thread-local API client.
    Should be called when a thread is done with its client.
    """
    if hasattr(_thread_local, 'client') and _thread_local.client:
        await _thread_local.client.aclose()
        _thread_local.client = None


def format_phone_number(phone: str) -> str:
    """
    Format phone number for API consumption.
    
    Handles Singapore numbers intelligently:
    - 8 digits starting with 9, 8, 3, or 6 → prepend +65
    - Already has + → use as-is
    - Otherwise → return as-is for API validation
    
    Args:
        phone: Raw phone number from user
        
    Returns:
        Formatted phone number
    """
    # Remove common separators
    phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    
    # Handle Singapore numbers (8 digits, specific prefixes)
    if len(phone) == 8 and phone[0] in "9836":
        return f"+65{phone}"
    
    # Already international format
    if phone.startswith("+"):
        return phone
    
    # For other formats, return as-is and let API validate
    return phone