"""
API Client for Realtime Tools
Singleton httpx client for making async API calls without blocking the event loop
"""
import httpx
from typing import Optional

# Singleton client instance
_client: Optional[httpx.AsyncClient] = None


async def get_api_client() -> httpx.AsyncClient:
    """
    Get or create the singleton API client.
    Uses connection pooling for efficiency.
    """
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url="http://localhost:8000",
            timeout=30.0,
            limits=httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10
            )
        )
    return _client


async def cleanup_api_client():
    """
    Cleanup the API client on shutdown.
    Should be called when the application terminates.
    """
    global _client
    if _client:
        await _client.aclose()
        _client = None


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