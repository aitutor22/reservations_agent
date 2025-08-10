"""
Restaurant RealtimeSession Manager
Manages the lifecycle and event processing for restaurant voice sessions

HANDOFF AUDIO DELAY IMPLEMENTATION
-----------------------------------
Since the OpenAI Realtime API doesn't support direct pause insertion in speech synthesis,
we implement a workaround by injecting silence buffers into the audio stream:

1. Detection: Monitor for handoff tool calls in the event stream
   - Tool names containing 'transfer', 'handoff', 'specialist', or 'sakura'
   - Triggered by 'response.function_call_arguments.done' events

2. Silence Generation: Create PCM16 silence buffer
   - 2 seconds of zeros at 24kHz sample rate (48,000 samples)
   - Converted to bytes for audio streaming

3. Injection: Insert silence immediately after handoff detection
   - Send silence buffer as audio_chunk to frontend
   - Frontend plays silence, creating natural pause

4. Recovery: Clear handoff flag when new agent starts speaking
   - Detected when 'response.audio.delta' arrives after handoff

This approach simulates realistic phone transfer delays without modifying
the AI's speech patterns or requiring API changes.
"""

import asyncio
from typing import Optional, Dict, Any
import base64
import numpy as np

from agents.realtime import RealtimeRunner
from .main_agent import main_agent, RESTAURANT_AGENT_CONFIG

# Maximum size for WebSocket frames (300KB for safety, well under 1MB limit)
# Reduced to 300KB to handle cases with handoff silence + large audio responses
MAX_WEBSOCKET_FRAME_SIZE = 300 * 1024  # 300KB in bytes

# Audio configuration for silence generation
AUDIO_SAMPLE_RATE = 24000  # 24kHz as required by OpenAI
HANDOFF_DELAY_SECONDS = 2.0  # 2 second pause after handoff


class RestaurantRealtimeSession:
    """Manages the restaurant realtime agent session"""
    
    def __init__(self):
        self.agent = None
        self.runner = None
        self.session = None
        self.session_context = None
        self.is_running = False
        self.handoff_pending = False  # Flag to track if we need to insert silence
        
    async def initialize(self):
        """Initialize the restaurant realtime agent"""
        print("[RestaurantAgent] Initializing agent...")
        
        # Use the main agent with handoff capability
        self.agent = main_agent
        
        # Configure the runner with restaurant settings
        self.runner = RealtimeRunner(
            starting_agent=self.agent,
            config=RESTAURANT_AGENT_CONFIG
        )
        
        print("[RestaurantAgent] Agent initialized with handoff capability")
        
    async def start_session(self):
        """Start the realtime session with proper context management"""
        if not self.runner:
            await self.initialize()
            
        print("[RestaurantAgent] Starting session...")
        # Use context manager for proper session lifecycle
        self.session_context = await self.runner.run()
        self.session = await self.session_context.__aenter__()
        self.is_running = True
        print("[RestaurantAgent] Session started")
        return self.session
    
    async def send_text(self, text: str):
        """Send text message to the session"""
        if self.session and self.is_running:
            if hasattr(self.session, 'send_text'):
                await self.session.send_text(text)
            elif hasattr(self.session, 'send_message'):
                await self.session.send_message(text)
            else:
                print(f"[RestaurantAgent] Text sending not supported")
    
    def generate_silence_buffer(self, duration_seconds: float = HANDOFF_DELAY_SECONDS) -> bytes:
        """Generate a buffer of silence (zeros) for the specified duration
        
        Args:
            duration_seconds: Duration of silence in seconds
            
        Returns:
            Bytes representing PCM16 silence
        """
        num_samples = int(AUDIO_SAMPLE_RATE * duration_seconds)
        silence_array = np.zeros(num_samples, dtype=np.int16)
        return silence_array.tobytes()
    
    async def send_audio(self, audio_data):
        """Send audio chunk to the realtime session
        
        Args:
            audio_data: Base64-encoded PCM16 audio string or raw bytes
        """
        if self.session and self.is_running:
            if hasattr(self.session, 'send_audio'):
                # Convert base64 to bytes if needed
                if isinstance(audio_data, str):
                    audio_bytes = base64.b64decode(audio_data)
                    # print(f"[RestaurantAgent] Received audio from frontend: {len(audio_data)} chars base64 -> {len(audio_bytes)} bytes PCM16")
                else:
                    audio_bytes = audio_data
                    # print(f"[RestaurantAgent] Received audio from frontend: {len(audio_bytes)} bytes")
                    
                # The RealtimeAgent expects raw PCM16 audio bytes
                await self.session.send_audio(audio_bytes)
                # print(f"[RestaurantAgent] Sent audio chunk to OpenAI session")
            else:
                print(f"[RestaurantAgent] Audio sending not supported yet")
    
    async def process_events(self):
        """Process events from the realtime session"""
        if not self.session:
            print("[RestaurantAgent] No session available")
            return
            
        try:
            print("[RestaurantAgent] Processing events...")
            
            async for event in self.session:
                event_type = event.type if hasattr(event, 'type') else str(type(event))
                
                # Handle different event types
                if event_type == "raw_model_event":
                    if hasattr(event, 'data') and hasattr(event.data, 'data'):
                        raw_data = event.data.data
                        inner_type = raw_data.get('type', '') if isinstance(raw_data, dict) else None
                        
                        if inner_type == 'response.audio_transcript.done':
                            transcript = raw_data.get('transcript', '')
                            if transcript:
                                print(f"[RestaurantAgent] Assistant: {transcript}")
                                yield {
                                    "type": "assistant_transcript",
                                    "transcript": transcript
                                }
                            
                        elif inner_type == 'conversation.item.input_audio_transcription.completed':
                            transcript = raw_data.get('transcript', '')
                            if transcript:
                                print(f"[RestaurantAgent] User: {transcript}")
                                yield {
                                    "type": "user_transcript",
                                    "transcript": transcript
                                }
                            
                        elif inner_type == 'response.audio.delta':
                            delta = raw_data.get('delta', '')
                            if delta:
                                # If this is the first audio after a handoff, we've finished the pause
                                if self.handoff_pending:
                                    print("[RestaurantAgent] New agent starting to speak after handoff")
                                    self.handoff_pending = False
                                
                                # Delta is base64-encoded PCM16 audio, decode to bytes
                                try:
                                    audio_bytes = base64.b64decode(delta)
                                    audio_size = len(audio_bytes)
                                    
                                    # Log size for debugging handoff issues
                                    if audio_size > 100000:  # Log large chunks (>100KB)
                                        print(f"[RestaurantAgent] Received large audio delta: {audio_size} bytes")
                                    
                                    # Check if audio chunk is too large for WebSocket
                                    if audio_size > MAX_WEBSOCKET_FRAME_SIZE:
                                        print(f"[RestaurantAgent] Large audio chunk ({audio_size} bytes), splitting into safe chunks...")
                                        
                                        # Calculate chunk size ensuring even byte boundary for PCM16
                                        chunk_size = MAX_WEBSOCKET_FRAME_SIZE
                                        if chunk_size % 2 != 0:
                                            chunk_size -= 1  # Make it even for PCM16 sample alignment
                                        
                                        # Split into chunks respecting PCM16 sample boundaries
                                        num_chunks = 0
                                        for i in range(0, audio_size, chunk_size):
                                            end = min(i + chunk_size, audio_size)
                                            
                                            # Ensure we don't split a PCM16 sample (2 bytes)
                                            if end < audio_size and (end - i) % 2 != 0:
                                                end -= 1
                                            
                                            chunk = audio_bytes[i:end]
                                            num_chunks += 1
                                            print(f"[RestaurantAgent] Sending audio chunk {num_chunks} ({len(chunk)} bytes)")
                                            
                                            yield {
                                                "type": "audio_chunk",
                                                "data": chunk
                                            }
                                    else:
                                        # Normal size, send as-is
                                        # Verify even byte count for PCM16
                                        if audio_size % 2 != 0:
                                            print(f"[RestaurantAgent] WARNING: Odd byte count ({audio_size}), may cause audio artifacts")
                                        
                                        yield {
                                            "type": "audio_chunk",
                                            "data": audio_bytes
                                        }
                                except Exception as e:
                                    print(f"[RestaurantAgent] Error decoding audio delta: {e}")
                                
                        elif inner_type == 'response.audio.done':
                            yield {"type": "audio_complete"}
                            
                        elif inner_type == 'session.created':
                            print("[RestaurantAgent] Session created")
                            yield {"type": "session_created"}
                            
                        elif inner_type == 'response.function_call_arguments.done':
                            # Tool was called
                            tool_name = raw_data.get('name', 'unknown')
                            print(f"[RestaurantAgent] Calling tool: {tool_name}")
                            
                            # Check if this is a handoff tool
                            # Handoff tools may have various name formats:
                            # - transfer_to_[agent_name]
                            # - [agent_name] (direct agent name)
                            # - handoff_to_[agent_name]
                            tool_name_lower = tool_name.lower()
                            is_handoff = (
                                'transfer' in tool_name_lower or 
                                'handoff' in tool_name_lower or
                                'specialist' in tool_name_lower
                            )
                            
                            # Check if this is a transfer back to the main agent
                            # Main agent does silent routing, so we don't need silence
                            is_main_agent_transfer = (
                                'ramenassistant' in tool_name_lower or 
                                'main' in tool_name_lower or
                                'routing' in tool_name_lower
                            )
                            
                            if is_handoff:
                                if is_main_agent_transfer:
                                    print(f"[RestaurantAgent] Transfer to MAIN AGENT (routing): {tool_name} - no silence needed")
                                    # Don't inject silence for main agent transfers (silent routing)
                                else:
                                    print(f"[RestaurantAgent] HANDOFF DETECTED to specialist: {tool_name}")
                                    self.handoff_pending = True
                                    
                                    # Send silence buffer immediately after handoff to specialist
                                    silence_buffer = self.generate_silence_buffer()
                                    print(f"[RestaurantAgent] Inserting {HANDOFF_DELAY_SECONDS}s silence ({len(silence_buffer)} bytes)")
                                    yield {
                                        "type": "audio_chunk",
                                        "data": silence_buffer
                                    }
                            else:
                                print(f"[RestaurantAgent] Regular tool call (not handoff): {tool_name}")
                            
                elif event_type == "audio":
                    if hasattr(event, 'data') and event.data:
                        audio_bytes = event.data
                        if isinstance(audio_bytes, bytes):
                            yield {
                                "type": "audio_chunk",
                                "data": audio_bytes
                            }
                            
                elif event_type == "audio_interrupted":
                    # User interrupted the assistant - just notify frontend
                    print("[RestaurantAgent] Audio interrupted by user")
                    yield {
                        "type": "audio_interrupted"
                    }
                    
                elif event_type == "audio_end":
                    # Audio response completed
                    print("[RestaurantAgent] Audio response completed")
                    yield {
                        "type": "audio_end"
                    }
                    
                elif event_type == "error":
                    error = getattr(event, 'error', 'Unknown error')
                    error_str = str(error)
                    print(f"[RestaurantAgent] Error: {error_str}")
                    
                    # Check if it's an audio truncation error - these are recoverable
                    if "already shorter than" in error_str:
                        print("[RestaurantAgent] Audio truncation error - continuing session")
                        yield {
                            "type": "warning",
                            "message": "Audio sync issue detected, continuing..."
                        }
                        # Don't break on truncation errors, they're recoverable
                    else:
                        yield {
                            "type": "error",
                            "error": error_str
                        }
                        self.is_running = False
                        break
                    
        except Exception as e:
            print(f"[RestaurantAgent] Error in process_events: {e}")
            self.is_running = False
            
    async def stop_session(self):
        """Stop the realtime session with proper cleanup"""
        print("[RestaurantAgent] Stopping session...")
        self.is_running = False
        
        # Properly exit the context manager
        if self.session_context:
            try:
                await self.session_context.__aexit__(None, None, None)
            except Exception as e:
                print(f"[RestaurantAgent] Error closing session context: {e}")
            self.session_context = None
            
        self.session = None
        print("[RestaurantAgent] Session stopped")


# Test function for standalone testing
async def test_restaurant_agent():
    """Test the restaurant agent standalone"""
    print("\n" + "="*60)
    print("Testing Restaurant Realtime Agent")
    print("="*60)
    
    session = RestaurantRealtimeSession()
    
    try:
        await session.initialize()
        await session.start_session()
        
        # Test messages
        test_queries = [
            "Hello! Welcome to Sakura Ramen House!",
            "What are your hours?",
            "Tell me about your menu",
            "I'd like to make a reservation for 4 people tomorrow at 7 PM"
        ]
        
        async def send_messages():
            await asyncio.sleep(2)
            for query in test_queries:
                print(f"\n[Test] Sending: {query}")
                await session.send_text(query)
                await asyncio.sleep(8)  # Wait for response
                
        async def process():
            async for event in session.process_events():
                if event["type"] == "error":
                    break
                    
        await asyncio.gather(send_messages(), process())
        
    except KeyboardInterrupt:
        print("\nInterrupted")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await session.stop_session()
        

if __name__ == "__main__":
    asyncio.run(test_restaurant_agent())