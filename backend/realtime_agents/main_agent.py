# -*- coding: utf-8 -*-
"""
Main Restaurant Agent with Handoff to Reservation Specialist

This module defines the restaurant's voice agents using a modular personality system.
The agents share a consistent voice personality while having role-specific behaviors.
"""

from agents.realtime import RealtimeAgent, realtime_handoff
from .voice_personality import get_agent_instructions, VOICE_SELECTION_NOTES, MODEL_SETTINGS_NOTES
from .reservation_agent import reservation_agent  # Import the consolidated reservation agent
from realtime_tools import (
    get_current_time,
    get_restaurant_hours,
    get_restaurant_contact_info,
    get_menu_info
)

# Create the information specialist agent with consistent personality
# This agent maintains the same voice personality while focusing on information
information_agent = RealtimeAgent(
    name="SakuraInformationSpecialist",
    instructions=get_agent_instructions("information") + """
    
You have been handed off a customer who needs information about our restaurant.

GREETING AFTER HANDOFF:
- Be brief and context-aware, don't re-introduce yourself
- Jump straight to helping with their question
- Use natural greetings like:
  - "Sure, I can help with that! What would you like to know?"
  - "Happy to help! What information do you need?"
  - "I can answer that for you. What's your question?"
  - "Of course! What would you like to know about our restaurant?"
- NEVER say "Hello, thank you for waiting"
- NEVER re-introduce the restaurant name

Your role is to provide detailed, accurate information about:
- Restaurant hours and days of operation
- Location, address, and directions
- Menu items, ramen varieties, and prices
- Daily specials and recommendations
- Restaurant policies and amenities
- Contact information

Use the provided tools to get accurate, up-to-date information:
- Use get_restaurant_hours() for operating hours
- Use get_restaurant_contact_info() for address and contact details
- Use get_menu_info() for menu details and prices
- Use get_current_time() if you need to check current time

Be enthusiastic about our food and provide helpful recommendations. 
If the customer wants to make a reservation after getting information, 
let them know you can help with that too.
    """,
    tools=[
        get_current_time,
        get_restaurant_hours,
        get_restaurant_contact_info,
        get_menu_info
    ]
)

# Create the main routing agent with handoff capability
# This agent embodies the restaurant's personality and handles initial routing
main_agent = RealtimeAgent(
    name="SakuraRamenAssistant",
    instructions=get_agent_instructions("main") + """
    
Your role is to warmly greet customers, answer basic questions, and route complex requests to appropriate specialists.

WHAT YOU CAN HANDLE DIRECTLY:
- Restaurant address and location
- Phone number and contact information
- Reject unrelated questions politely
Use the get_restaurant_contact_info() tool for address and phone inquiries.

ROUTING INSTRUCTIONS:
1. DETAILED INFORMATION REQUESTS → Information Specialist
   - Questions about hours, operating times
   - Menu inquiries, prices, ramen varieties
   - Daily specials, recommendations
   - Any detailed restaurant information beyond basic contact
   Use one of these natural transitions:
   - "Let me get someone who can help with that."
   - "I'll connect you with someone who knows all our menu details."
   - "One moment, let me transfer you."

2. RESERVATION REQUESTS → Reservation Specialist
   - Making a reservation or booking a table
   - Checking availability
   - Modifying existing reservations
   - Looking up existing reservations
   Use one of these natural transitions:
   - "I'll transfer you to our reservation specialist right away. One moment, please."
   - "Let me connect you with reservations. One moment."
   - "I'll get someone who can help with that. Just a moment."

IMPORTANT:
- Keep your initial greeting brief and friendly
- Answer basic address/phone questions yourself
- For menu, hours, or detailed info, hand off to information specialist
- For reservations, hand off to reservation specialist
- Politely decline unrelated requests
- If unsure about complex questions, hand off to information specialist

Example greetings:
- 'Hello! Thank you for calling Sakura Ramen House. How can I help you?'
- 'Thank you for calling Sakura Ramen House. What can I do for you today?'

RESTAURANT DETAILS:
Location: 78 Boat Quay, Singapore 049866
Phone: +65 6877 9888
    """,
    tools=[get_restaurant_contact_info],  # Main agent can answer basic location/phone questions
    handoffs=[
        realtime_handoff(information_agent, tool_description_override="Transfer to information specialist for restaurant hours, menu, and detailed inquiries"),
        realtime_handoff(reservation_agent, tool_description_override="Transfer to reservation specialist for booking tables and checking availability")
    ]
)

# Configuration for the RealtimeRunner (applies to all agents in the session)
# Voice and model settings are carefully chosen to match the restaurant's personality
# See voice_personality.py for detailed rationale on voice selection and settings
RESTAURANT_AGENT_CONFIG = {
    "model_settings": {
        "model_name": "gpt-4o-realtime-preview-2024-12-17",
        "voice": "shimmer",  # Clear female voice, good for hospitality
        # Alternative voices to try if needed:
        # "nova" - energetic female voice
        # "alloy" - neutral/female voice
        # "echo" - softer female voice
        "modalities": ["text", "audio"],
        "temperature": 0.8,  # Natural variation without losing consistency
        "turn_detection": {
            "type": "server_vad",
            "threshold": 0.5,  # Balanced sensitivity for phone conversations
            "prefix_padding_ms": 300,  # Captures complete utterances
            "silence_duration_ms": 500  # Natural pause detection
        }
    },
    # Handoff configuration for smooth transitions
    "handoff_settings": {
        "transition_delay_ms": 1500,  # 1.5 second pause to simulate real transfer
        "play_transition_sound": False,  # Could add a brief tone/music in future
        "preserve_context": True  # Pass conversation context to next agent
    }
}

# Log personality configuration status
print(f"[Voice Personality] Loaded agents with personality configuration")
print(f"[Voice Config] Using voice: {RESTAURANT_AGENT_CONFIG['model_settings']['voice']}")