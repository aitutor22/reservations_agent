"""
FastAPI Main Application
Restaurant Voice Reservation Agent Backend
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List
import asyncio
import json
import uuid
from datetime import datetime
import httpx
import os

from config import config
from services.openai_service import get_openai_service
from knowledge.vector_store_manager import setup_knowledge_base
from database import get_db, init_db, close_db
from sqlalchemy.ext.asyncio import AsyncSession
from models.reservation import ReservationCreate, ReservationUpdate, ReservationResponse
from services.reservation_service import get_reservation_service


# Session management
active_sessions: Dict[str, Dict[str, Any]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    print("Starting Restaurant Voice Reservation Agent...")
    
    # Initialize database
    try:
        await init_db()
    except Exception as db_error:
        print(f"Warning: Could not initialize database: {db_error}")
        print("Continuing without database support...")
    
    # try:
    #     # List all vector stores from OpenAI
    #     print("\n" + "="*60)
    #     print("Fetching Vector Stores from OpenAI API...")
    #     print("="*60)
        
    #     api_key = os.getenv("OPENAI_API_KEY") or config.OPENAI_API_KEY
    #     if api_key:
    #         async with httpx.AsyncClient() as client:
    #             try:
    #                 response = await client.get(
    #                     "https://api.openai.com/v1/vector_stores",
    #                     headers={
    #                         "Authorization": f"Bearer {api_key}",
    #                         "OpenAI-Beta": "assistants=v2"
    #                     }
    #                 )
                    
    #                 if response.status_code == 200:
    #                     vector_stores = response.json()
    #                     print(f"\nTotal Vector Stores: {len(vector_stores.get('data', []))}")
    #                     print("-"*60)
                        
    #                     for store in vector_stores.get('data', []):
    #                         print(f"ID: {store.get('id')}")
    #                         print(f"Name: {store.get('name', 'Unnamed')}")
    #                         print(f"Created: {store.get('created_at')}")
    #                         print(f"File Counts: {store.get('file_counts', {})}")
    #                         print(f"Status: {store.get('status')}")
    #                         print(f"Bytes: {store.get('usage_bytes', 0)}")
    #                         print("-"*40)
                        
    #                     if not vector_stores.get('data'):
    #                         print("No vector stores found.")
    #                 else:
    #                     print(f"Failed to fetch vector stores: {response.status_code}")
    #                     print(f"Response: {response.text}")
                        
    #             except Exception as e:
    #                 print(f"Error fetching vector stores: {e}")
    #     else:
    #         print("No OpenAI API key configured - skipping vector store listing")
        
    #     print("="*60 + "\n")
        
        # Initialize knowledge base
        print("Initializing knowledge base...")
        try:
            vector_store_id = setup_knowledge_base()
            print(f"Knowledge base ready with vector store: {vector_store_id}")
        except Exception as kb_error:
            print(f"Warning: Could not initialize knowledge base: {kb_error}")
            print("Continuing without vector store support...")
        
        # Initialize OpenAI service
        service = get_openai_service()
        print("OpenAI service initialized")
        
    except Exception as e:
        print(f"Error during startup: {e}")
        # Continue anyway to allow fixing configuration
    
    yield
    
    # Shutdown
    print("Shutting down...")
    service = get_openai_service()
    service.cleanup()
    
    # Close database connections
    await close_db()
    
    print("Cleanup complete")


# Create FastAPI app
app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": config.APP_NAME,
        "version": config.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }


# OpenAI Realtime API ephemeral token generation
@app.post("/api/realtime/session")
async def create_realtime_session():
    """
    Generate ephemeral token for WebRTC connection to OpenAI Realtime API
    The token is valid for 1 minute and enables direct browser-to-OpenAI communication
    """
    try:
        # Check if API key is configured
        api_key = os.getenv("OPENAI_API_KEY") or config.OPENAI_API_KEY
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not configured"
            )
        
        # Create ephemeral token via OpenAI API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/realtime/sessions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-realtime-preview-2024-12-17",
                    "voice": "verse",  # Options: alloy, echo, fable, onyx, nova, verse
                    "instructions": config.GREETING_AGENT_INSTRUCTIONS,
                    "turn_detection": {
                        "type": "server_vad",  # Server voice activity detection
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 500
                    },
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "temperature": 0.8
                }
            )
            
            if response.status_code != 200:
                error_detail = response.text
                print(f"OpenAI API error: {response.status_code} - {error_detail}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to create realtime session: {error_detail}"
                )
            
            data = response.json()
            
            # Log session creation (without exposing the key)
            session_id = str(uuid.uuid4())
            print(f"Created realtime session: {session_id}")
            
            # Return ephemeral token and configuration
            return {
                "session_id": session_id,
                "ephemeral_key": data.get("client_secret", {}).get("value"),
                "expires_at": data.get("client_secret", {}).get("expires_at"),
                "model": data.get("model"),
                "voice": data.get("voice"),
                "instructions": data.get("instructions"),
                "turn_detection": data.get("turn_detection"),
                "message": "Ephemeral token generated successfully. Valid for 60 seconds."
            }
            
    except httpx.RequestError as e:
        print(f"Network error creating realtime session: {e}")
        raise HTTPException(
            status_code=503,
            detail="Network error connecting to OpenAI API"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error creating realtime session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create realtime session: {str(e)}"
        )


# Test Realtime Agent endpoint
@app.websocket("/ws/realtime/test")
async def test_realtime_websocket(websocket: WebSocket):
    """WebSocket endpoint for testing RealtimeAgent with WebRTC audio"""
    await websocket.accept()
    session_id = str(uuid.uuid4())
    
    print(f"[TestRealtime WS] New connection: {session_id}")
    
    # Import here to avoid circular dependencies
    from test_realtime_agent import TestRealtimeSession
    
    session_manager = TestRealtimeSession()
    
    try:
        # Initialize the realtime agent
        await session_manager.initialize()
        await session_manager.start_session()
        
        # Send initial success message
        await websocket.send_json({
            "type": "session_started",
            "session_id": session_id
        })
        
        # Create tasks for bidirectional communication
        async def handle_incoming():
            """Handle incoming WebSocket messages (audio from browser)"""
            try:
                while True:
                    data = await websocket.receive()
                    
                    if "text" in data:
                        # Handle text messages
                        message = json.loads(data["text"])
                        msg_type = message.get("type")
                        
                        if msg_type == "text_message":
                            # Handle text input from frontend
                            text = message.get("text")
                            if text and hasattr(session_manager.session, 'send_text'):
                                print(f"[TestRealtime WS] Sending text: {text}")
                                await session_manager.session.send_text(text)
                            elif text:
                                print(f"[TestRealtime WS] Text message not supported yet: {text}")
                                
                        elif msg_type == "audio_chunk":
                            # Forward audio to realtime session
                            audio_data = message.get("data")
                            if audio_data:
                                await session_manager.process_audio_chunk(audio_data)
                                
                        elif msg_type == "end_session":
                            print(f"[TestRealtime WS] Ending session {session_id}")
                            break
                            
                    elif "bytes" in data:
                        # Handle binary audio data directly
                        await session_manager.process_audio_chunk(data["bytes"])
                        
            except WebSocketDisconnect:
                print(f"[TestRealtime WS] Client disconnected: {session_id}")
            except Exception as e:
                print(f"[TestRealtime WS] Error handling incoming: {e}")
                
        async def handle_outgoing():
            """Handle outgoing events from realtime session"""
            try:
                async for event in session_manager.process_events():
                    # Send events back to browser
                    if event["type"] == "audio_chunk":
                        # Send audio as binary
                        await websocket.send_bytes(event["data"])
                    else:
                        # Send other events as JSON
                        await websocket.send_json(event)
                        
            except Exception as e:
                print(f"[TestRealtime WS] Error handling outgoing: {e}")
                
        # Run both tasks concurrently
        await asyncio.gather(
            handle_incoming(),
            handle_outgoing()
        )
        
    except Exception as e:
        print(f"[TestRealtime WS] Session error: {e}")
        await websocket.send_json({
            "type": "error",
            "error": str(e)
        })
    finally:
        await session_manager.stop_session()
        print(f"[TestRealtime WS] Session closed: {session_id}")
        try:
            await websocket.close()
        except:
            pass


# Session management endpoints
@app.post("/api/session/create")
async def create_session():
    """Create a new session"""
    session_id = str(uuid.uuid4())
    
    active_sessions[session_id] = {
        "id": session_id,
        "created_at": datetime.utcnow().isoformat(),
        "state": "greeting",
        "context": {}
    }
    
    # Reset the service for new session
    service = get_openai_service()
    service.reset_session()
    
    return {
        "session_id": session_id,
        "status": "created",
        "message": "Session created successfully"
    }


@app.delete("/api/session/{session_id}")
async def end_session(session_id: str):
    """End a session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del active_sessions[session_id]
    
    return {
        "session_id": session_id,
        "status": "ended",
        "message": "Session ended successfully"
    }


# Message processing endpoint (for testing without WebSocket)
@app.post("/api/message")
async def process_message(data: dict):
    """Process a text message (for testing)"""
    session_id = data.get("session_id")
    message = data.get("message")
    
    if not session_id or session_id not in active_sessions:
        raise HTTPException(status_code=400, detail="Invalid session ID")
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    # Process message with OpenAI service
    service = get_openai_service()
    response, state = await service.process_message(message)
    
    # Update session state
    active_sessions[session_id]["state"] = state
    
    return {
        "response": response,
        "state": state,
        "session_id": session_id
    }


# Import the WebSocket handler
from websocket_handler import handle_websocket_connection

# WebSocket endpoint for real-time communication
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time audio and text communication"""
    # Use the new WebSocket handler
    await handle_websocket_connection(websocket, session_id)


# Restaurant information endpoints (REST fallback)
@app.get("/api/restaurant/info")
async def get_restaurant_info():
    """Get basic restaurant information"""
    return {
        "name": config.RESTAURANT_NAME,
        "phone": config.RESTAURANT_PHONE,
        "address": config.RESTAURANT_ADDRESS,
        "hours": {
            "monday_thursday": "11:30 AM - 9:30 PM",
            "friday_saturday": "11:30 AM - 10:30 PM",
            "sunday": "11:30 AM - 9:00 PM"
        }
    }


@app.post("/api/restaurant/query")
async def query_restaurant_info(data: dict):
    """Query restaurant information using information agent"""
    query = data.get("query")
    
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    service = get_openai_service()
    
    # Process query with information agent directly
    if service.information_agent:
        result = service.information_agent.process_query(query)
        
        if result["success"]:
            return {
                "response": result["response"],
                "success": True
            }
        else:
            return {
                "response": "Unable to process query",
                "success": False,
                "error": result.get("error")
            }
    else:
        raise HTTPException(status_code=503, detail="Information service unavailable")


# Reservation endpoints
@app.post("/api/reservations", response_model=ReservationResponse)
async def create_reservation(
    reservation: ReservationCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new reservation"""
    try:
        service = await get_reservation_service(db)
        result = await service.create_reservation(reservation)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create reservation: {str(e)}")


@app.get("/api/reservations/{phone_number}", response_model=ReservationResponse)
async def get_reservation(
    phone_number: str,
    db: AsyncSession = Depends(get_db)
):
    """Get reservation by phone number"""
    service = await get_reservation_service(db)
    reservation = await service.get_reservation_by_phone(phone_number)
    
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    return reservation


@app.put("/api/reservations/{phone_number}", response_model=ReservationResponse)
async def update_reservation(
    phone_number: str,
    update_data: ReservationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing reservation"""
    service = await get_reservation_service(db)
    reservation = await service.update_reservation(phone_number, update_data)
    
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    return reservation


@app.delete("/api/reservations/{phone_number}")
async def cancel_reservation(
    phone_number: str,
    db: AsyncSession = Depends(get_db)
):
    """Cancel a reservation"""
    service = await get_reservation_service(db)
    deleted = await service.delete_reservation(phone_number)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    return {"message": "Reservation cancelled successfully"}


@app.get("/api/reservations", response_model=List[ReservationResponse])
async def list_reservations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """List all reservations with optional filtering"""
    service = await get_reservation_service(db)
    reservations = await service.list_all_reservations(skip=skip, limit=limit, filter_date=date)
    return reservations


@app.post("/api/reservations/check-availability")
async def check_availability(
    data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Check availability for a given date/time"""
    check_date = data.get("date")
    check_time = data.get("time")
    party_size = data.get("party_size", 2)
    
    if not check_date or not check_time:
        raise HTTPException(status_code=400, detail="Date and time are required")
    
    service = await get_reservation_service(db)
    availability = await service.check_availability(check_date, check_time, party_size)
    return availability


# Admin endpoints for testing
@app.get("/api/admin/sessions")
async def list_sessions():
    """List all active sessions (admin endpoint)"""
    return {
        "count": len(active_sessions),
        "sessions": list(active_sessions.values())
    }


@app.post("/api/admin/reset")
async def reset_service():
    """Reset the OpenAI service (admin endpoint)"""
    service = get_openai_service()
    service.reset_session()
    
    # Clear all sessions
    active_sessions.clear()
    
    return {
        "status": "reset",
        "message": "Service reset successfully"
    }


if __name__ == "__main__":
    import uvicorn
    
    print(f"Starting server on {config.HOST}:{config.PORT}")
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG
    )