#!/usr/bin/env python3
"""
Simple WebSocket test client for testing text message handling
"""

import asyncio
import websockets
import json
import uuid


async def test_websocket():
    """Test the WebSocket connection with text messages"""
    
    # Generate a session ID
    session_id = str(uuid.uuid4())
    uri = f"ws://localhost:8000/ws/{session_id}"
    
    print(f"Connecting to WebSocket at {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected successfully!")
            
            # Wait for connection confirmation
            response = await websocket.recv()
            print(f"Server: {response}")
            
            # Test messages
            test_messages = [
                {"type": "session:start"},
                {"type": "text:message", "text": "Hello, server!"},
                {"type": "text:message", "text": "Can you echo this?"},
                {"type": "ping", "timestamp": "2024-01-01T12:00:00"},
                {"type": "unknown_type", "data": "test"},
                {"type": "text:message", "text": "Final message"},
                {"type": "session:end"}
            ]
            
            for msg in test_messages:
                # Send message
                print(f"\nSending: {msg}")
                await websocket.send(json.dumps(msg))
                
                # Receive response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    response_data = json.loads(response)
                    print(f"Response: {response_data}")
                    
                    # Break if session ended
                    if response_data.get("type") == "session:ended":
                        print("\nSession ended by server")
                        break
                        
                except asyncio.TimeoutError:
                    print("No response received (timeout)")
                except websockets.exceptions.ConnectionClosed:
                    print("Connection closed by server")
                    break
            
            print("\nTest completed!")
            
    except websockets.exceptions.WebSocketException as e:
        print(f"WebSocket error: {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("WebSocket Test Client")
    print("=" * 50)
    print("Make sure the FastAPI server is running on port 8000")
    print("=" * 50)
    
    asyncio.run(test_websocket())