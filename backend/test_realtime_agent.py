#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Realtime Agent
Simple implementation to verify WebRTC to Backend to OpenAI Realtime API flow
"""

import asyncio
from datetime import datetime
from typing import Optional
import json

from agents import function_tool
from agents.realtime import RealtimeAgent, RealtimeRunner


@function_tool
def get_current_time() -> str:
    """Get the current time."""
    current_time = datetime.now().strftime("%I:%M %p")
    print(f"[Tool Called] get_current_time() -> {current_time}")
    return f"The current time is {current_time}"


@function_tool
def get_restaurant_hours() -> str:
    """Get the restaurant operating hours."""
    print("[Tool Called] get_restaurant_hours()")
    return """
    Our hours are:
    - Monday to Thursday: 11:30 AM - 9:30 PM
    - Friday to Saturday: 11:30 AM - 10:30 PM
    - Sunday: 11:30 AM - 9:00 PM
    """


class TestRealtimeSession:
    """Manages a test realtime agent session"""
    
    def __init__(self):
        self.agent = None
        self.runner = None
        self.session = None
        self.is_running = False
        
    async def initialize(self):
        """Initialize the realtime agent and runner"""
        print("[TestRealtime] Initializing agent...")
        
        # Create a simple test agent
        self.agent = RealtimeAgent(
            name="TestAssistant",
            instructions=(
                "You are a helpful test assistant for a ramen restaurant. "
                "Keep responses very brief and conversational. "
                "You can tell the current time and restaurant hours if asked. "
                "Greet users warmly but briefly."
            ),
            tools=[get_current_time, get_restaurant_hours]
        )
        
        # Configure the runner
        self.runner = RealtimeRunner(
            starting_agent=self.agent,
            config={
                "model_settings": {
                    "model_name": "gpt-4o-realtime-preview-2024-12-17",
                    "voice": "verse",  # Match current config
                    "modalities": ["text", "audio"],
                    "temperature": 0.8,
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 500  # Match current config
                    }
                }
            }
        )
        
        print("[TestRealtime] Agent and runner initialized")
        
    async def start_session(self):
        """Start the realtime session"""
        if not self.runner:
            await self.initialize()
            
        print("[TestRealtime] Starting session...")
        self.session = await self.runner.run()
        self.is_running = True
        print("[TestRealtime] Session started successfully")
        return self.session
    
    async def process_audio_chunk(self, audio_data: bytes):
        """Send audio chunk to the realtime session"""
        if self.session and self.is_running:
            # The session should handle audio input
            # This will depend on the actual SDK implementation
            await self.session.send_audio(audio_data)
    
    async def process_events(self):
        """Process events from the realtime session"""
        if not self.session:
            print("[TestRealtime] No session available")
            return
            
        async with self.session:
            print("[TestRealtime] Processing events...")
            
            async for event in self.session:
                event_type = event.type if hasattr(event, 'type') else str(type(event))
                
                # Handle different event types based on the SDK's actual event structure
                if event_type == "raw_model_event":
                    # Extract the actual event from the raw model event
                    if hasattr(event, 'data') and hasattr(event.data, 'data'):
                        raw_data = event.data.data
                        inner_type = raw_data.get('type', '') if isinstance(raw_data, dict) else None
                        
                        # Handle specific inner event types
                        if inner_type == 'response.audio_transcript.done':
                            transcript = raw_data.get('transcript', 'No transcript')
                            print(f"[TestRealtime] Assistant said: {transcript}")
                            yield {
                                "type": "assistant_transcript",
                                "transcript": transcript
                            }
                            
                        elif inner_type == 'conversation.item.input_audio_transcription.completed':
                            transcript = raw_data.get('transcript', 'No transcript')
                            print(f"[TestRealtime] User said: {transcript}")
                            yield {
                                "type": "user_transcript",
                                "transcript": transcript
                            }
                            
                        elif inner_type == 'response.audio.delta':
                            # Audio chunk - don't print binary data
                            delta = raw_data.get('delta', '')
                            if delta:
                                # Just note that audio was received without printing the data
                                print(f"[TestRealtime] Audio chunk received ({len(delta)} bytes)")
                                yield {
                                    "type": "audio_chunk",
                                    "data": delta
                                }
                                
                        elif inner_type == 'response.audio.done':
                            print("[TestRealtime] Audio response complete")
                            
                        elif inner_type == 'session.created':
                            print("[TestRealtime] Session created successfully")
                            yield {
                                "type": "session_created"
                            }
                            
                        elif inner_type == 'session.updated':
                            # Session config updated - don't print the whole config
                            print("[TestRealtime] Session configuration updated")
                            
                        elif inner_type == 'response.done':
                            print("[TestRealtime] Response complete")
                            
                        elif inner_type == 'rate_limits.updated':
                            # Skip rate limit updates
                            pass
                            
                        else:
                            # For other inner types, just log the type
                            if inner_type:
                                print(f"[TestRealtime] Event: {inner_type}")
                                
                elif event_type == "audio":
                    # Audio event with binary data - don't print the data
                    if hasattr(event, 'data') and event.data:
                        audio_bytes = event.data
                        if isinstance(audio_bytes, bytes):
                            print(f"[TestRealtime] Audio received ({len(audio_bytes)} bytes)")
                            yield {
                                "type": "audio_chunk", 
                                "data": audio_bytes
                            }
                    else:
                        print(f"[TestRealtime] Audio event (no data)")
                        
                elif event_type == "history_updated":
                    # History update - just note it happened
                    print("[TestRealtime] Conversation history updated")
                    
                elif event_type == "agent_end":
                    print("[TestRealtime] Agent turn complete")
                    
                elif event_type == "audio_end":
                    print("[TestRealtime] Audio stream ended")
                    
                elif event_type == "error":
                    error = getattr(event, 'error', 'Unknown error')
                    print(f"[TestRealtime] Error: {error}")
                    yield {
                        "type": "error",
                        "error": str(error)
                    }
                    self.is_running = False
                    break
                    
                else:
                    # For truly unhandled events, print minimal info
                    print(f"[TestRealtime] Unhandled event type: {event_type}")
                    
    async def stop_session(self):
        """Stop the realtime session"""
        print("[TestRealtime] Stopping session...")
        self.is_running = False
        if self.session:
            # Close the session properly
            # This depends on SDK implementation
            pass
        print("[TestRealtime] Session stopped")


async def test_realtime_agent():
    """Test function to run the realtime agent standalone"""
    print("\n" + "="*60)
    print("Testing Realtime Agent")
    print("="*60)
    
    session_manager = TestRealtimeSession()
    
    try:
        # Initialize and start session
        await session_manager.initialize()
        session = await session_manager.start_session()
        
        print("\nSession is ready! Sending test messages...")
        print("-"*60)
        
        # Send test messages to trigger responses
        test_messages = [
            "Hello! How are you?",
            "What time is it?",
            "What are your hours?",
            "Can you tell me about the restaurant?"
        ]
        
        async def send_test_messages():
            """Send test text messages to the agent"""
            await asyncio.sleep(1)  # Wait for session to be fully ready
            
            for message in test_messages:
                print(f"\n[Test] Sending: {message}")
                
                # Send text message to the session
                # Check which method is available
                if hasattr(session_manager.session, 'send_text'):
                    await session_manager.session.send_text(message)
                    print(f"[Test] Message sent via send_text")
                elif hasattr(session_manager.session, 'send_message'):
                    await session_manager.session.send_message(message)
                    print(f"[Test] Message sent via send_message")
                elif hasattr(session_manager.session, 'send'):
                    # Try sending as a dict
                    await session_manager.session.send({"text": message})
                    print(f"[Test] Message sent via send")
                else:
                    print(f"[Test] Warning: No suitable send method found on session")
                    print(f"[Test] Available methods: {dir(session_manager.session)}")
                
                # Wait between messages
                await asyncio.sleep(5)
        
        # Create a task to process events
        async def process_all_events():
            """Process all events from the session"""
            async for event in session_manager.process_events():
                if event["type"] == "error":
                    print(f"\nError occurred: {event['error']}")
                    break
        
        # Run both tasks concurrently
        await asyncio.gather(
            send_test_messages(),
            process_all_events()
        )
                
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError in test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await session_manager.stop_session()
        print("\nTest completed")
        print("="*60)


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_realtime_agent())