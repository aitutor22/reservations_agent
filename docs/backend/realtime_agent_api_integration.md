# RealtimeAgent API Integration Architecture

## Overview

This document explains how OpenAI RealtimeAgent tools integrate with REST APIs, covering architecture patterns, performance considerations, and best practices for building production-ready voice agents.

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Why REST API Calls from Tools?](#why-rest-api-calls-from-tools)
3. [httpx vs requests: The Critical Choice](#httpx-vs-requests-the-critical-choice)
4. [Performance Analysis](#performance-analysis)
5. [Implementation Patterns](#implementation-patterns)
6. [Error Handling](#error-handling)
7. [Optimization Strategies](#optimization-strategies)
8. [Best Practices](#best-practices)

## Architecture Overview

The standard architecture for RealtimeAgent tools making API calls:

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────┐
│   OpenAI    │────►│ Function Tool│────►│  REST API   │────►│ Database │
│ RealtimeAgent│     │  @function   │     │   FastAPI   │     │PostgreSQL│
└─────────────┘     └──────────────┘     └─────────────┘     └──────────┘
     (1)                  (2)                  (3)                 (4)

(1) Agent decides to call tool based on user intent
(2) Tool executes, making async HTTP call
(3) API processes business logic and validation
(4) Database persists data
```

### Why This Architecture?

This layered approach is **industry standard** because it provides:
- **Separation of Concerns**: Voice handling separate from business logic
- **Reusability**: Same API serves web, mobile, and voice interfaces
- **Maintainability**: Business logic centralized in API layer
- **Scalability**: Each layer can scale independently
- **Security**: API handles authentication and validation

## Why REST API Calls from Tools?

### It's Standard Practice

Making REST API calls from function tools is the normal, recommended approach used by:

1. **OpenAI's Examples**
   - Weather tools → Weather APIs
   - Search tools → Search APIs
   - Database tools → Database APIs

2. **Enterprise AI Agents**
   - Salesforce Einstein → Salesforce APIs
   - GitHub Copilot → GitHub APIs
   - Slack bots → Slack APIs

3. **Common Production Patterns**
   ```python
   @function_tool
   async def book_flight(...):
       # Calls airline booking API
       return await airline_api.create_booking(...)

   @function_tool  
   async def check_inventory(...):
       # Calls inventory management API
       return await inventory_api.get_stock(...)

   @function_tool
   async def process_payment(...):
       # Calls payment gateway API (Stripe, etc.)
       return await stripe_api.create_charge(...)
   ```

### Benefits Over Direct Database Access

While you *could* have tools directly access the database, REST APIs provide:

1. **Business Logic Centralization**
   ```python
   # API endpoint handles ALL business rules
   @app.post("/api/reservations")
   async def create_reservation(data: ReservationCreate):
       # Validation
       validate_reservation_time(data.time)
       
       # Business rules
       check_blackout_dates(data.date)
       verify_capacity(data.party_size)
       prevent_duplicates(data.phone)
       
       # Create reservation
       return await service.create_reservation(data)
   ```

2. **Multiple Client Support**
   - Voice agents use the API
   - Web interface uses the API
   - Mobile apps use the API
   - Third-party integrations use the API

3. **Proper Validation and Security**
   - Input validation at API layer
   - Authentication/authorization
   - Rate limiting
   - Audit logging

## httpx vs requests: The Critical Choice

### The Fundamental Difference

```python
# httpx - GOOD for RealtimeAgent (non-blocking)
@function_tool
async def make_reservation(...) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post("/api/reservations", json=data)
    return response.text

# requests - BAD for RealtimeAgent (blocks event loop)
@function_tool
async def make_reservation(...) -> str:
    response = requests.post("http://localhost:8000/api/reservations", json=data)
    # This blocks! Even in async function, requests.post is synchronous
    return response.text
```

### Why httpx is Required for Voice Agents

The RealtimeAgent runs in an async event loop to handle:
- Real-time audio streaming
- Concurrent tool calls
- WebSocket communication
- Multiple simultaneous conversations

Using `requests` would **block the entire event loop**, causing:
- Audio stuttering/delays
- Frozen voice responses
- WebSocket timeouts
- Poor user experience

### Performance Comparison

```python
# Scenario: Agent needs to check availability for 3 time slots

# httpx - Concurrent execution (~1 second total)
async def check_multiple_slots():
    async with httpx.AsyncClient() as client:
        tasks = [
            client.post("/api/check", json={"time": "18:00"}),
            client.post("/api/check", json={"time": "19:00"}),
            client.post("/api/check", json={"time": "20:00"})
        ]
        responses = await asyncio.gather(*tasks)
    return responses

# requests - Sequential execution (~3 seconds total)
def check_multiple_slots():
    responses = []
    for time in ["18:00", "19:00", "20:00"]:
        responses.append(requests.post("http://localhost:8000/api/check", 
                                       json={"time": time}))
    return responses
```

### Real-World Impact on Voice UX

**With blocking (requests):**
```
User: "Check if you have tables at 6, 7, or 8 PM"
[0ms]    Start processing speech
[100ms]  Speech recognized, calling tool
[100ms]  Check 6 PM (requests.post blocks for 500ms)
[600ms]  Check 7 PM (requests.post blocks for 500ms)  
[1100ms] Check 8 PM (requests.post blocks for 500ms)
[1600ms] Generate response
[1700ms] Start speaking response
Total: 1.7 seconds of silence (bad UX!)
```

**With async (httpx):**
```
User: "Check if you have tables at 6, 7, or 8 PM"
[0ms]    Start processing speech
[100ms]  Speech recognized, calling tools
[100ms]  Check 6, 7, 8 PM concurrently (all three at once)
[600ms]  All responses received
[700ms]  Generate response
[800ms]  Start speaking response  
Total: 0.8 seconds (good UX!)
```

## Performance Analysis

### Typical Latency Breakdown

Understanding where time is spent in a voice interaction:

```
User speaks: "Book a table for 4 at 7pm"
├─ Speech-to-text:          ~200-300ms  (OpenAI Whisper)
├─ LLM processing:          ~300-500ms  (Deciding to call tool)
├─ Tool execution:          ~50-200ms   (Your API call) ← We are here
│  ├─ Network (localhost):  ~1-5ms
│  ├─ API processing:       ~10-50ms
│  └─ Database query:       ~10-100ms
├─ LLM response generation: ~200-300ms  (Formulating response)
└─ Text-to-speech:          ~200-300ms  (OpenAI TTS)

Total: ~1000-1600ms (1-1.6 seconds)
```

**Key Insight**: The API call (~50-200ms) is only 5-12% of total latency!

### Is It Fast Enough?

**Yes!** The REST API approach adds minimal latency while providing significant architectural benefits:

- **Direct DB Access**: ~20-50ms
- **REST API Call**: ~50-200ms
- **Additional Latency**: ~30-150ms (negligible in voice context)

This extra latency is imperceptible to users but provides:
- Centralized business logic
- Proper validation
- Security controls
- Audit logging
- Multi-client support

## Implementation Patterns

### Basic API Client Pattern

```python
# backend/realtime_tools/api_client.py
import httpx
from typing import Optional

# Singleton client for connection reuse
_client: Optional[httpx.AsyncClient] = None

async def get_api_client() -> httpx.AsyncClient:
    """Get or create the singleton API client"""
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
    """Cleanup on shutdown"""
    global _client
    if _client:
        await _client.aclose()
        _client = None
```

### Function Tool Implementation

```python
# backend/realtime_tools/reservation.py
from agents import function_tool
from .api_client import get_api_client

@function_tool
async def make_reservation(
    name: str, 
    phone: str, 
    date: str, 
    time: str, 
    party_size: int, 
    special_requests: str = ""
) -> str:
    """
    Create a reservation through the API.
    
    Args:
        name: Guest name
        phone: Contact phone number  
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM format
        party_size: Number of guests
        special_requests: Any dietary restrictions or special needs
    """
    client = await get_api_client()
    
    try:
        response = await client.post(
            "/api/reservations",
            json={
                "customer_name": name,
                "phone_number": phone,
                "reservation_date": date,
                "reservation_time": time,
                "party_size": party_size,
                "special_requests": special_requests
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return f"✅ Reservation confirmed! Confirmation number: {data['id']}"
        elif response.status_code == 400:
            error = response.json().get('detail', 'Invalid reservation data')
            return f"❌ Unable to create reservation: {error}"
        else:
            return "❌ Unable to create reservation. Please try again."
            
    except httpx.TimeoutException:
        return "❌ The system is taking too long to respond. Please try again."
    except httpx.RequestError:
        return "❌ Connection error. Please try again later."
```

### Advanced Pattern with Retries

```python
import asyncio
from typing import Optional

@function_tool
async def check_availability(
    date: str,
    time: str,
    party_size: int,
    retry_count: int = 3
) -> str:
    """Check table availability with automatic retry"""
    client = await get_api_client()
    
    for attempt in range(retry_count):
        try:
            response = await client.post(
                "/api/reservations/check-availability",
                json={
                    "date": date,
                    "time": time,
                    "party_size": party_size
                },
                timeout=5.0  # Shorter timeout for availability checks
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("available"):
                    return f"✅ Tables available for {party_size} people at {time}"
                else:
                    # Suggest alternatives if available
                    alts = data.get("alternatives", [])
                    if alts:
                        times = ", ".join(alts[:3])
                        return f"❌ No tables at {time}. Available times: {times}"
                    return f"❌ No tables available at {time}"
                    
        except (httpx.TimeoutException, httpx.RequestError) as e:
            if attempt < retry_count - 1:
                await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
                continue
            return "❌ Unable to check availability. Please try again."
    
    return "❌ System is currently unavailable."
```

## Error Handling

### Error Handling Strategy

Different error types require different user responses:

```python
@function_tool
async def handle_reservation_request(...) -> str:
    """Comprehensive error handling example"""
    client = await get_api_client()
    
    try:
        response = await client.post("/api/reservations", json=data)
        
        # Success
        if response.status_code == 200:
            return format_success_response(response.json())
        
        # Client errors (4xx)
        elif response.status_code == 400:
            # Validation error - extract details
            detail = response.json().get('detail', 'Invalid data')
            return f"I couldn't make that reservation: {detail}"
            
        elif response.status_code == 404:
            return "I couldn't find that information."
            
        elif response.status_code == 409:
            # Conflict - e.g., duplicate reservation
            return "You already have a reservation. Would you like to modify it?"
            
        elif response.status_code == 429:
            # Rate limited
            return "The system is busy. Please wait a moment."
        
        # Server errors (5xx)
        elif response.status_code >= 500:
            return "Our reservation system is temporarily unavailable."
        
        else:
            return "Something went wrong. Please try again."
            
    except httpx.TimeoutException:
        return "The system is taking longer than expected. Please try again."
        
    except httpx.ConnectError:
        return "I'm having trouble connecting to our reservation system."
        
    except httpx.RequestError as e:
        # Log the actual error for debugging
        print(f"Request error: {e}")
        return "I encountered an issue. Please try again."
```

### User-Friendly Error Messages

Always translate technical errors into natural language:

```python
ERROR_MESSAGES = {
    "INVALID_DATE": "That date doesn't seem right. Could you tell me the date again?",
    "PAST_DATE": "I can't make reservations for past dates. When would you like to come?",
    "TOO_LARGE": "We can't accommodate parties larger than 20. Could you split into smaller groups?",
    "BLACKOUT": "We're closed for a private event that day. How about another date?",
    "NO_CAPACITY": "We're fully booked at that time. Would you like to try a different time?",
}

@function_tool
async def make_reservation(...) -> str:
    # ... make API call ...
    
    if response.status_code == 400:
        error_code = response.json().get('error_code')
        return ERROR_MESSAGES.get(error_code, "I couldn't complete that reservation.")
```

## Optimization Strategies

### 1. Connection Pooling

Reuse connections to minimize latency:

```python
class APIClient:
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url="http://localhost:8000",
            limits=httpx.Limits(
                max_keepalive_connections=5,  # Keep 5 connections alive
                max_connections=10,            # Maximum 10 concurrent
                keepalive_expiry=30           # Keep alive for 30 seconds
            ),
            timeout=httpx.Timeout(
                connect=5.0,     # Connection timeout
                read=10.0,       # Read timeout
                write=5.0,       # Write timeout
                pool=5.0         # Pool timeout
            )
        )
```

### 2. Concurrent Requests

Make multiple API calls simultaneously:

```python
@function_tool
async def find_best_time(
    date: str,
    preferred_times: list[str],
    party_size: int
) -> str:
    """Check multiple times concurrently"""
    client = await get_api_client()
    
    # Create tasks for all time checks
    tasks = [
        check_single_time(client, date, time, party_size)
        for time in preferred_times
    ]
    
    # Run all checks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Find first available time
    for time, result in zip(preferred_times, results):
        if isinstance(result, dict) and result.get("available"):
            return f"✅ Great! I found availability at {time}"
    
    return "❌ No tables available at your preferred times"
```

### 3. Caching for Static Data

Cache responses that don't change frequently:

```python
from functools import lru_cache
from datetime import datetime, timedelta

# Cache with TTL
class CachedResponse:
    def __init__(self, data, ttl_seconds=300):
        self.data = data
        self.expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
    
    @property
    def is_valid(self):
        return datetime.now() < self.expires_at

_cache = {}

@function_tool
async def get_restaurant_hours() -> str:
    """Get restaurant hours with caching"""
    cache_key = "restaurant_hours"
    
    # Check cache
    if cache_key in _cache and _cache[cache_key].is_valid:
        return _cache[cache_key].data
    
    # Fetch from API
    client = await get_api_client()
    response = await client.get("/api/restaurant/hours")
    
    if response.status_code == 200:
        data = format_hours(response.json())
        _cache[cache_key] = CachedResponse(data, ttl_seconds=3600)  # 1 hour
        return data
    
    return "Unable to retrieve hours"
```

### 4. Batch Operations

Combine multiple operations into single API calls:

```python
@function_tool
async def check_multiple_dates(
    dates: list[str],
    time: str,
    party_size: int
) -> str:
    """Check availability for multiple dates in one call"""
    client = await get_api_client()
    
    # Single API call with multiple dates
    response = await client.post(
        "/api/reservations/check-availability-bulk",
        json={
            "dates": dates,
            "time": time,
            "party_size": party_size
        }
    )
    
    if response.status_code == 200:
        available = response.json()["available_dates"]
        if available:
            return f"✅ Available on: {', '.join(available)}"
        return "❌ No availability on those dates"
```

## Best Practices

### DO's

1. **Use async/await throughout**
   ```python
   @function_tool
   async def my_tool():  # ✅ async function
       client = await get_api_client()  # ✅ await async calls
       response = await client.post(...)  # ✅ await HTTP calls
   ```

2. **Implement proper error handling**
   ```python
   try:
       response = await client.post(...)
       # Handle different status codes
   except httpx.RequestError:
       # Return user-friendly error
   ```

3. **Use connection pooling**
   ```python
   # Create client once, reuse for all requests
   _client = httpx.AsyncClient(limits=httpx.Limits(...))
   ```

4. **Make concurrent requests when possible**
   ```python
   results = await asyncio.gather(*tasks)
   ```

5. **Configure appropriate timeouts**
   ```python
   timeout=httpx.Timeout(connect=5.0, read=10.0)
   ```

### DON'T's

1. **Don't use synchronous libraries**
   ```python
   # ❌ BAD - blocks event loop
   import requests
   response = requests.get(...)
   
   # ✅ GOOD - async
   import httpx
   response = await client.get(...)
   ```

2. **Don't create new clients for each request**
   ```python
   # ❌ BAD - inefficient
   async def my_tool():
       async with httpx.AsyncClient() as client:
           ...
   
   # ✅ GOOD - reuse client
   async def my_tool():
       client = await get_api_client()
       ...
   ```

3. **Don't expose technical errors to users**
   ```python
   # ❌ BAD
   return f"Error: {str(exception)}"
   
   # ✅ GOOD
   return "I'm having trouble with that. Please try again."
   ```

4. **Don't ignore timeout scenarios**
   ```python
   # ❌ BAD - no timeout
   response = await client.post(url)
   
   # ✅ GOOD - explicit timeout
   response = await client.post(url, timeout=10.0)
   ```

5. **Don't make sequential calls when concurrent is possible**
   ```python
   # ❌ BAD - sequential
   for item in items:
       await process_item(item)
   
   # ✅ GOOD - concurrent
   await asyncio.gather(*[process_item(item) for item in items])
   ```

## Summary

Making REST API calls from RealtimeAgent function tools is:
- **Standard practice** in the industry
- **Fast enough** for voice interactions (adds only 50-200ms)
- **Architecturally correct** (separation of concerns)
- **Scalable** (supports multiple clients)
- **Maintainable** (centralized business logic)

The key requirements are:
1. Use **httpx** for async HTTP calls (never requests)
2. Implement **proper error handling** with user-friendly messages
3. Use **connection pooling** for efficiency
4. Make **concurrent requests** when possible
5. Follow **async/await patterns** throughout

The benefits far outweigh the minimal latency cost, providing a clean, maintainable, and production-ready architecture for voice agents.