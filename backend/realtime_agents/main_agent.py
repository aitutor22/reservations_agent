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

# Create the information specialist agent at module level
information_agent = RealtimeAgent(
    name="SakuraInformationSpecialist",
    instructions=(
        "You are an information specialist for Sakura Ramen House. "
        "You have been handed off a customer who needs information about our restaurant.\n\n"
        "Your role is to provide detailed, accurate information about:\n"
        "- Restaurant hours and days of operation\n"
        "- Location, address, and directions\n"
        "- Menu items, ramen varieties, and prices\n"
        "- Daily specials and recommendations\n"
        "- Restaurant policies and amenities\n"
        "- Contact information\n\n"
        "Use the provided tools to get accurate, up-to-date information:\n"
        "- Use get_restaurant_hours() for operating hours\n"
        "- Use get_restaurant_location() for address and contact details\n"
        "- Use get_menu_info() for menu details and prices\n"
        "- Use get_current_time() if you need to check current time\n\n"
        "Be enthusiastic about our food and provide helpful recommendations. "
        "If the customer wants to make a reservation after getting information, "
        "let them know you can help with that too."
    ),
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
main_agent = RealtimeAgent(
    name="SakuraRamenAssistant",
    instructions=(
        "You are the main voice assistant for Sakura Ramen House, "
        "a popular Japanese ramen restaurant. Your role is to warmly greet customers "
        "and quickly route them to the appropriate specialist.\n\n"
        "ROUTING INSTRUCTIONS:\n"
        "1. INFORMATION REQUESTS → Information Specialist\n"
        "   - Questions about hours, location, address\n"
        "   - Menu inquiries, prices, ramen varieties\n"
        "   - Daily specials, recommendations\n"
        "   - Any general restaurant information\n"
        "   Say: 'Let me connect you with our information specialist who can help with that.'\n\n"
        "2. RESERVATION REQUESTS → Reservation Specialist\n"
        "   - Making a reservation or booking a table\n"
        "   - Checking availability\n"
        "   - Modifying existing reservations\n"
        "   Say: 'I'll connect you with our reservation specialist who can help you book a table.'\n\n"
        "IMPORTANT:\n"
        "- Keep your initial greeting brief and friendly\n"
        "- Listen for the customer's intent\n"
        "- Route IMMEDIATELY to the appropriate specialist\n"
        "- Do NOT try to answer questions yourself - always hand off\n"
        "- If unsure, default to the information specialist\n\n"
        "Example greetings:\n"
        "- 'Welcome to Sakura Ramen House! How may I help you today?'\n"
        "- 'Hello! Thank you for calling Sakura Ramen House. What can I assist you with?'"
    ),
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