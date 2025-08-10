#!/usr/bin/env python3
"""
Test script for Restaurant Agent with Handoff
Tests the main greeting agent and its handoff to reservation specialist
"""

import sys
import os
# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from realtime_agents import RestaurantRealtimeSession


async def test_handoff_flow():
    """Test the agent handoff from greeting to reservation specialist"""
    print("\n" + "="*60)
    print("Testing Restaurant Agent with Handoff Capability")
    print("="*60)
    
    session = RestaurantRealtimeSession()
    
    try:
        await session.initialize()
        await session.start_session()
        
        # Test conversation flow that should trigger handoff
        test_queries = [
            # Initial greeting - handled by main agent
            "Hello! Can you tell me about your restaurant?",
            
            # Menu inquiry - handled by main agent
            "What kinds of ramen do you serve?",
            
            # Hours inquiry - handled by main agent  
            "What are your opening hours?",
            
            # This should trigger handoff to reservation specialist
            "I'd like to make a reservation for dinner",
            
            # After handoff, reservation specialist handles these
            "4 people",
            "Tomorrow at 7 PM",
            "My name is John Smith",
            "My phone is 555-1234"
        ]
        
        async def send_messages():
            await asyncio.sleep(2)
            for i, query in enumerate(test_queries):
                print(f"\n[Test {i+1}] User: {query}")
                await session.send_text(query)
                
                # Give more time for reservation-related responses
                if "reservation" in query.lower() or i >= 3:
                    await asyncio.sleep(10)  # More time for reservation flow
                else:
                    await asyncio.sleep(6)  # Regular response time
                    
        async def process():
            async for event in session.process_events():
                if event["type"] == "assistant_transcript":
                    print(f"[Assistant]: {event['transcript']}")
                elif event["type"] == "user_transcript":
                    print(f"[User Heard]: {event['transcript']}")
                elif event["type"] == "error":
                    print(f"[Error]: {event['error']}")
                    break
                    
        # Run both tasks concurrently
        await asyncio.gather(send_messages(), process())
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test error: {e}")
    finally:
        await session.stop_session()
        print("\n" + "="*60)
        print("Test completed")
        print("="*60)


if __name__ == "__main__":
    print("\n🧪 Starting Restaurant Agent Handoff Test")
    print("This test will simulate a conversation that triggers agent handoff")
    print("from the main greeting agent to the reservation specialist.\n")
    
    asyncio.run(test_handoff_flow())