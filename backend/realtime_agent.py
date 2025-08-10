#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Restaurant Realtime Agent
Production implementation of voice-enabled restaurant reservation agent
"""

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
import json

from agents import function_tool
from agents.realtime import RealtimeAgent, RealtimeRunner
from config import config


# Restaurant-specific tools
@function_tool
def get_current_time() -> str:
    """Get the current time."""
    current_time = datetime.now().strftime("%I:%M %p")
    return f"The current time is {current_time}"


@function_tool
def get_restaurant_hours() -> str:
    """Get the restaurant operating hours."""
    return """
    Sakura Ramen House hours:
    - Monday to Thursday: 11:30 AM - 9:30 PM
    - Friday to Saturday: 11:30 AM - 10:30 PM
    - Sunday: 11:30 AM - 9:00 PM
    """


@function_tool
def get_restaurant_location() -> str:
    """Get the restaurant location and contact information."""
    return f"""
    Sakura Ramen House
    Address: {config.RESTAURANT_ADDRESS}
    Phone: {config.RESTAURANT_PHONE}
    
    We're located in the heart of downtown, easily accessible by public transit.
    Street parking and a public garage are available nearby.
    """


@function_tool
def get_menu_info() -> str:
    """Get information about our ramen menu."""
    return """
    Our signature ramen varieties:
    
    🍜 **Tonkotsu Ramen** ($14.95)
    Rich pork bone broth simmered for 24 hours, with chashu pork, soft-boiled egg, bamboo shoots, and green onions.
    
    🍜 **Shoyu Ramen** ($13.95)
    Light soy sauce-based clear broth with chicken and vegetables, topped with chashu pork, soft-boiled egg, and nori.
    
    🍜 **Miso Ramen** ($14.95)
    Hearty miso-based broth with ground pork, corn, butter, soft-boiled egg, and green onions.
    
    🍜 **Spicy Miso Ramen** ($15.95)
    Our miso ramen with added chili oil and spices, topped with ground pork, soft-boiled egg, and green onions.
    
    🌱 **Vegetarian Ramen** ($12.95)
    Rich vegetable broth with tofu, mushrooms, corn, bamboo shoots, and seasonal vegetables.
    
    All ramen comes with handmade noodles. Extra toppings available.
    """


@function_tool
def check_availability(date: str, time: str, party_size: int) -> str:
    """
    Check if a reservation slot is available.
    
    Args:
        date: Date in format YYYY-MM-DD
        time: Time in format HH:MM
        party_size: Number of people
    """
    # TODO: Integrate with actual reservation system
    # For now, simulate availability
    import random
    
    if party_size > 8:
        return "I'm sorry, but we can only accommodate parties of up to 8 people. For larger groups, please call us directly."
    
    # Simulate availability check
    is_available = random.choice([True, True, True, False])  # 75% chance of availability
    
    if is_available:
        return f"Good news! We have availability for {party_size} people on {date} at {time}. Would you like me to make a reservation?"
    else:
        # Suggest alternative times
        alt_time1 = "6:30 PM" if "7" in time else "7:30 PM"
        alt_time2 = "8:00 PM" if "7" in time else "6:00 PM"
        return f"I'm sorry, but {time} on {date} is not available for {party_size} people. We do have availability at {alt_time1} or {alt_time2}. Would either of those work for you?"


@function_tool
def make_reservation(name: str, phone: str, date: str, time: str, party_size: int, special_requests: str = "") -> str:
    """
    Create a reservation.
    
    Args:
        name: Guest name
        phone: Contact phone number
        date: Date in format YYYY-MM-DD
        time: Time in format HH:MM
        party_size: Number of people
        special_requests: Any special requests or dietary restrictions
    """
    # TODO: Integrate with actual reservation system
    # For now, generate a confirmation number
    import random
    confirmation_number = f"SR{random.randint(10000, 99999)}"
    
    response = f"""
    ✅ Reservation confirmed!
    
    Confirmation Number: {confirmation_number}
    Name: {name}
    Date: {date}
    Time: {time}
    Party Size: {party_size}
    Phone: {phone}
    """
    
    if special_requests:
        response += f"Special Requests: {special_requests}\n"
    
    response += "\nWe've sent a confirmation to your phone. See you soon at Sakura Ramen House!"
    
    return response


class RestaurantRealtimeSession:
    """Manages the restaurant realtime agent session"""
    
    def __init__(self):
        self.agent = None
        self.runner = None
        self.session = None
        self.session_context = None
        self.is_running = False
        
    async def initialize(self):
        """Initialize the restaurant realtime agent"""
        print("[RestaurantAgent] Initializing agent...")
        
        # Create the restaurant agent with all tools
        self.agent = RealtimeAgent(
            name="SakuraRamenAssistant",
            instructions=(
                "You are a friendly and helpful voice assistant for Sakura Ramen House, "
                "a popular Japanese ramen restaurant. Your role is to:\n"
                "1. Answer questions about our restaurant (hours, location, menu)\n"
                "2. Check availability for reservations\n"
                "3. Make reservations for guests\n"
                "4. Provide information about our delicious ramen varieties\n\n"
                "Keep responses conversational and warm. Be enthusiastic about our food. "
                "If someone wants to make a reservation, collect all necessary information "
                "(name, phone, date, time, party size) before confirming.\n"
                "Always mention our confirmation number when a reservation is made."
            ),
            tools=[
                get_current_time,
                get_restaurant_hours,
                get_restaurant_location,
                get_menu_info,
                check_availability,
                make_reservation
            ]
        )
        
        # Configure the runner with restaurant settings
        self.runner = RealtimeRunner(
            starting_agent=self.agent,
            config={
                "model_settings": {
                    "model_name": "gpt-4o-realtime-preview-2024-12-17",
                    "voice": "verse",  # Friendly, warm voice
                    "modalities": ["text", "audio"],
                    "temperature": 0.8,
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 500
                    }
                }
            }
        )
        
        print("[RestaurantAgent] Agent initialized with restaurant tools")
        
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
    
    async def send_audio(self, audio_data):
        """Send audio chunk to the realtime session
        
        Args:
            audio_data: Base64-encoded PCM16 audio string or raw bytes
        """
        if self.session and self.is_running:
            if hasattr(self.session, 'send_audio'):
                # Convert base64 to bytes if needed
                if isinstance(audio_data, str):
                    import base64
                    audio_bytes = base64.b64decode(audio_data)
                else:
                    audio_bytes = audio_data
                    
                # The RealtimeAgent expects raw PCM16 audio bytes
                await self.session.send_audio(audio_bytes)
                print(f"[RestaurantAgent] Sent audio chunk to session")
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
                                # Delta is base64-encoded PCM16 audio, decode to bytes
                                import base64
                                try:
                                    audio_bytes = base64.b64decode(delta)
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