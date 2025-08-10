"""
Main Restaurant Agent with Handoff to Reservation Specialist

This module defines the restaurant's voice agents using a modular personality system.
The agents share a consistent voice personality while having role-specific behaviors.
"""

from agents.realtime import RealtimeAgent, realtime_handoff
from .voice_personality import get_agent_instructions, VOICE_SELECTION_NOTES, MODEL_SETTINGS_NOTES
from realtime_tools import (
    get_current_time,
    get_restaurant_hours,
    get_restaurant_location,
    get_menu_info,
    check_availability,
    make_reservation
)

# Create the reservation specialist agent with consistent personality
# This agent maintains the same voice personality as the main agent but focuses on reservations
reservation_agent = RealtimeAgent(
    name="SakuraReservationSpecialist",
    instructions=get_agent_instructions("reservation") + """
    
# TOOLS AVAILABLE
- Use check_availability() to verify table availability for requested date/time
- Use make_reservation() to create and confirm the booking

# RESTAURANT DETAILS
Location: 78 Boat Quay, Singapore 049866
Phone: +65 6877 9888
    """,
    tools=[
        check_availability,
        make_reservation
    ]
)

# Create the main greeting agent with handoff capability
# This agent embodies the restaurant's personality and handles initial interactions
main_agent = RealtimeAgent(
    name="SakuraRamenAssistant",
    instructions=get_agent_instructions("main") + """
    
# TOOLS AVAILABLE
- Use get_current_time() for current time information
- Use get_restaurant_location() for our address at 78 Boat Quay, Singapore 049866
- Use get_restaurant_hours() for our operating hours
- Use get_menu_info() for our delicious ramen varieties and prices

# RESTAURANT DETAILS
Location: 78 Boat Quay, Singapore 049866
Phone: +65 6877 9888
Specialty: Authentic Japanese ramen with rich, flavorful broths
    """,
    tools=[
        get_current_time,
        get_restaurant_hours,
        get_restaurant_location,
        get_menu_info
    ],
    handoffs=[
        realtime_handoff(reservation_agent, tool_description_override="Transfer to reservation specialist for booking tables and checking availability")
    ]
)

# Configuration for the RealtimeRunner (applies to all agents in the session)
# Voice and model settings are carefully chosen to match the restaurant's personality
# See voice_personality.py for detailed rationale on voice selection and settings
RESTAURANT_AGENT_CONFIG = {
    "model_settings": {
        "model_name": "gpt-4o-realtime-preview-2024-12-17",
        "voice": "verse",  # Warm, friendly voice perfect for hospitality
        "modalities": ["text", "audio"],
        "temperature": 0.8,  # Natural variation without losing consistency
        "turn_detection": {
            "type": "server_vad",
            "threshold": 0.5,  # Balanced sensitivity for phone conversations
            "prefix_padding_ms": 300,  # Captures complete utterances
            "silence_duration_ms": 500  # Natural pause detection
        }
    }
}

# Export configuration notes for documentation
__doc__ += f"\n\nVoice Configuration Notes:\n{VOICE_SELECTION_NOTES}\n\nModel Settings Rationale:\n{MODEL_SETTINGS_NOTES}"