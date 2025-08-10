"""
WebSocket handler for Restaurant RealtimeAgent
Handles voice communication between browser and OpenAI Realtime API
"""
import base64
import asyncio
import json
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws/realtime/agent")
async def restaurant_realtime_websocket(websocket: WebSocket):
    """WebSocket endpoint for Restaurant RealtimeAgent with voice capabilities"""
    await websocket.accept()
    session_id = str(uuid.uuid4())
    
    print(f"[RestaurantAgent WS] New connection: {session_id}")
    
    # Import the guardrail-enabled restaurant agent session
    from realtime_agents.guardrail_session import GuardrailRestaurantSession
    
    session_manager = GuardrailRestaurantSession()
    
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
                            if text:
                                result = await session_manager.send_text(text)
                                # Check if guardrail rejected the input
                                if result and isinstance(result, dict) and result.get("type") == "guardrail_rejection":
                                    await websocket.send_json({
                                        "type": "guardrail_rejection",
                                        "message": result.get("message", "Input rejected by security policy")
                                    })
                                
                        elif msg_type == "audio_chunk":
                            # Forward base64-encoded PCM16 audio to realtime session
                            audio_base64 = message.get("audio")
                            if audio_base64:
                                # RealtimeAgent expects base64-encoded PCM16
                                await session_manager.send_audio(audio_base64)
                                
                        elif msg_type == "end_audio":
                            # User finished sending audio
                            print(f"[RestaurantAgent WS] End of audio input")
                            # The session will process this with VAD
                            
                        elif msg_type == "end_session":
                            print(f"[RestaurantAgent WS] Ending session {session_id}")
                            break
                            
                    elif "bytes" in data:
                        # Handle binary audio data directly
                        # Convert bytes to base64 for RealtimeAgent
                        audio_base64 = base64.b64encode(data["bytes"]).decode('utf-8')
                        await session_manager.send_audio(audio_base64)
                        
            except WebSocketDisconnect:
                print(f"[RestaurantAgent WS] Client disconnected: {session_id}")
                raise  # Re-raise to exit the task properly
            except Exception as e:
                print(f"[RestaurantAgent WS] Error handling incoming: {e}")
                # Don't crash on errors, just log and continue
                # This allows the session to recover from transient issues
                await asyncio.sleep(0.1)  # Small delay to prevent tight error loops
                
        async def handle_outgoing():
            """Handle outgoing events from realtime session"""
            try:
                async for event in session_manager.process_events():
                    try:
                        # Send events back to browser
                        if event["type"] == "audio_chunk":
                            # Send audio as binary
                            chunk_data = event["data"]
                            chunk_size = len(chunk_data)
                            
                            # Safety check: If chunk is still too large, split it
                            # This shouldn't happen with our 300KB limit, but provides safety
                            MAX_SAFE_SIZE = 300 * 1024  # 300KB safe limit
                            
                            if chunk_size > MAX_SAFE_SIZE:
                                print(f"[RestaurantAgent WS] WARNING: Large chunk ({chunk_size} bytes), splitting for safety")
                                
                                # Split into safe chunks respecting PCM16 boundaries
                                safe_chunk_size = MAX_SAFE_SIZE
                                if safe_chunk_size % 2 != 0:
                                    safe_chunk_size -= 1  # Ensure even for PCM16
                                
                                for i in range(0, chunk_size, safe_chunk_size):
                                    end = min(i + safe_chunk_size, chunk_size)
                                    # Ensure we don't split a PCM16 sample
                                    if end < chunk_size and (end - i) % 2 != 0:
                                        end -= 1
                                    
                                    sub_chunk = chunk_data[i:end]
                                    await websocket.send_bytes(sub_chunk)
                            elif event["type"] in ["guardrail_rejection", "guardrail_warning"]:
                                # Send guardrail events with high priority
                                print(f"[RestaurantAgent WS] Guardrail event: {event['type']}")
                                await websocket.send_json(event)
                            else:
                                # Normal size, send as-is
                                await websocket.send_bytes(chunk_data)
                        else:
                            # Send other events as JSON
                            await websocket.send_json(event)
                    except Exception as send_error:
                        print(f"[RestaurantAgent WS] Error sending event: {send_error}")
                        # Continue processing other events
                        
            except Exception as e:
                print(f"[RestaurantAgent WS] Error handling outgoing: {e}")
                raise  # Re-raise to exit the task
                
        # Run both tasks concurrently with error isolation
        # return_exceptions=True prevents one task failure from canceling the other
        results = await asyncio.gather(
            handle_incoming(),
            handle_outgoing(),
            return_exceptions=True
        )
        
        # Check if any task failed
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                task_name = "handle_incoming" if i == 0 else "handle_outgoing"
                print(f"[RestaurantAgent WS] Task {task_name} failed: {result}")
                # Continue - the other task may still be running
        
    except Exception as e:
        print(f"[RestaurantAgent WS] Session error: {e}")
        await websocket.send_json({
            "type": "error",
            "error": str(e)
        })
    finally:
        # Get guardrail statistics before closing
        if hasattr(session_manager, 'get_statistics'):
            stats = session_manager.get_statistics()
            print(f"[RestaurantAgent WS] Guardrail stats for session {session_id}: {stats}")
        
        await session_manager.stop_session()
        print(f"[RestaurantAgent WS] Session closed: {session_id}")
        try:
            await websocket.close()
        except:
            pass