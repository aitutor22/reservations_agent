"""
WebSocket Handler
Manages real-time text communication for the Restaurant Voice Agent
"""

from fastapi import WebSocket, WebSocketDisconnect
import json
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and message handling"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept and store a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected: session_id={session_id}")
    
    def disconnect(self, session_id: str):
        """Remove a WebSocket connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected: session_id={session_id}")
    
    async def send_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send a JSON message to a specific WebSocket"""
        await websocket.send_json(message)
        logger.info(f"Sent message: {message}")
    
    async def broadcast(self, message: Dict[str, Any], session_id: str = None):
        """Broadcast a message to all or specific connection"""
        if session_id and session_id in self.active_connections:
            await self.send_message(self.active_connections[session_id], message)
        else:
            for connection in self.active_connections.values():
                await self.send_message(connection, message)


# Create global connection manager instance
manager = ConnectionManager()


async def handle_websocket_connection(websocket: WebSocket, session_id: str):
    """
    Handle WebSocket connection for text-based communication
    
    Args:
        websocket: The WebSocket connection
        session_id: Unique session identifier
    """
    # Connect the WebSocket
    await manager.connect(websocket, session_id)
    
    # Send initial connection confirmation
    await manager.send_message(websocket, {
        "type": "connection:established",
        "session_id": session_id,
        "message": "WebSocket connection established successfully"
    })
    
    try:
        while True:
            # Receive text message from client
            data = await websocket.receive_text()
            logger.info(f"Received raw data: {data}")
            
            try:
                # Parse JSON message
                message = json.loads(data)
                message_type = message.get("type", "unknown")
                
                logger.info(f"Parsed message type: {message_type}, content: {message}")
                
                # Handle different message types
                if message_type == "text:message":
                    # Echo the text message back
                    text_content = message.get("text", "")
                    logger.info(f"Processing text message: {text_content}")
                    print('received and call backend api')
                    # call backend api
                    
                    # Send echo response
                    await manager.send_message(websocket, {
                        "type": "text:response",
                        "text": f"Received: {text_content}",
                        "echo": True,
                        "original": text_content
                    })
                
                elif message_type == "ping":
                    # Respond to heartbeat
                    await manager.send_message(websocket, {
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    })
                    logger.info("Responded to ping")
                
                elif message_type == "session:start":
                    # Handle session start
                    await manager.send_message(websocket, {
                        "type": "session:started",
                        "session_id": session_id,
                        "message": "Session started successfully"
                    })
                    logger.info(f"Session started: {session_id}")
                
                elif message_type == "session:end":
                    # Handle session end
                    await manager.send_message(websocket, {
                        "type": "session:ended",
                        "session_id": session_id,
                        "message": "Session ending..."
                    })
                    logger.info(f"Session ending: {session_id}")
                    break
                
                else:
                    # Unknown message type
                    logger.warning(f"Unknown message type: {message_type}")
                    await manager.send_message(websocket, {
                        "type": "error",
                        "code": "UNKNOWN_MESSAGE_TYPE",
                        "message": f"Unknown message type: {message_type}",
                        "received": message
                    })
            
            except json.JSONDecodeError as e:
                # Handle JSON parsing errors
                logger.error(f"JSON decode error: {e}")
                await manager.send_message(websocket, {
                    "type": "error",
                    "code": "INVALID_JSON",
                    "message": "Invalid JSON format",
                    "details": str(e)
                })
            
            except Exception as e:
                # Handle other processing errors
                logger.error(f"Processing error: {e}")
                await manager.send_message(websocket, {
                    "type": "error",
                    "code": "PROCESSING_ERROR",
                    "message": "Error processing message",
                    "details": str(e)
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected normally: session_id={session_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        
        # Try to send error message before closing
        try:
            await manager.send_message(websocket, {
                "type": "error",
                "code": "WEBSOCKET_ERROR",
                "message": "WebSocket error occurred",
                "details": str(e)
            })
        except:
            pass
    
    finally:
        # Clean up connection
        manager.disconnect(session_id)
        logger.info(f"Cleaned up connection for session: {session_id}")