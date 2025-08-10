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

# Create the information specialist agent with consistent personality
# This agent maintains the same voice personality while focusing on information
information_agent = RealtimeAgent(
    name="SakuraInformationSpecialist",
    instructions=get_agent_instructions("information") + """
    
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
    ]
)

# Create the reservation specialist agent at module level
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

# Create the main routing agent with handoff capability
# This agent embodies the restaurant's personality and handles initial routing
main_agent = RealtimeAgent(
    name="SakuraRamenAssistant",
    instructions=get_agent_instructions("main") + """
    
# ROUTING INSTRUCTIONS
1. INFORMATION REQUESTS → Information Specialist
   - Questions about hours, location, address
   - Menu inquiries, prices, ramen varieties
   - Daily specials, recommendations
   - Any general restaurant information
   Say: "Let me connect you with our information specialist who can help with that."

2. RESERVATION REQUESTS → Reservation Specialist
   - Making a reservation or booking a table
   - Checking availability
   - Modifying existing reservations
   Say: "I'll connect you with our reservation specialist who can help you book a table."

# IMPORTANT ROUTING GUIDELINES
- Listen for the customer's intent
- Route IMMEDIATELY to the appropriate specialist
- Do NOT try to answer questions yourself - always hand off
- If unsure, default to the information specialist

# RESTAURANT DETAILS
Location: 78 Boat Quay, Singapore 049866
Phone: +65 6877 9888
    """,
    tools=[],  # Main agent doesn't need tools - just routes
    handoffs=[
        realtime_handoff(information_agent, tool_description_override="Transfer to information specialist for restaurant details, hours, menu, and general inquiries"),
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
    }
}

# Log personality configuration status
print(f"[Voice Personality] Loaded agents with personality configuration")
print(f"[Voice Config] Using voice: {RESTAURANT_AGENT_CONFIG['model_settings']['voice']}")