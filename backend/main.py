"""
FastAPI Main Application
Restaurant Voice Reservation Agent Backend
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
import asyncio
import json
import uuid
from datetime import datetime

from config import config
from services.openai_service import get_openai_service
from knowledge.vector_store_manager import setup_knowledge_base


# Session management
active_sessions: Dict[str, Dict[str, Any]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    print("Starting Restaurant Voice Reservation Agent...")
    
    try:
        # Initialize knowledge base
        print("Initializing knowledge base...")
        vector_store_id = setup_knowledge_base()
        print(f"Knowledge base ready with vector store: {vector_store_id}")
        
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


# WebSocket endpoint for real-time communication
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time audio and text communication"""
    await websocket.accept()
    
    # Verify session
    if session_id not in active_sessions:
        await websocket.send_json({
            "type": "error",
            "code": "INVALID_SESSION",
            "message": "Invalid session ID"
        })
        await websocket.close()
        return
    
    service = get_openai_service()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = message_data.get("type")
            
            if message_type == "audio:chunk":
                # Handle audio chunk (placeholder for OpenAI Realtime API)
                # This would be processed through OpenAI's speech-to-text
                await websocket.send_json({
                    "type": "audio:processing",
                    "message": "Audio processing not yet implemented"
                })
                
            elif message_type == "text:message":
                # Process text message
                user_message = message_data.get("text", "")
                
                # Send partial transcript
                await websocket.send_json({
                    "type": "transcript:partial",
                    "text": user_message,
                    "role": "user"
                })
                
                # Process with OpenAI service
                response, state = await service.process_message(user_message)
                
                # Update session state
                active_sessions[session_id]["state"] = state
                
                # Send agent response
                await websocket.send_json({
                    "type": "transcript:final",
                    "text": response,
                    "role": "agent"
                })
                
                # Send state update
                await websocket.send_json({
                    "type": "agent:state",
                    "state": state,
                    "context": service.get_session_context()
                })
                
            elif message_type == "session:end":
                # End session
                break
                
            elif message_type == "ping":
                # Heartbeat
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        # Clean up session
        if session_id in active_sessions:
            del active_sessions[session_id]


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
    """Query restaurant information using knowledge agent"""
    query = data.get("query")
    
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    service = get_openai_service()
    
    # Process query with knowledge agent directly
    if service.knowledge_agent:
        result = service.knowledge_agent.process_query(query)
        
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
        raise HTTPException(status_code=503, detail="Knowledge service unavailable")


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