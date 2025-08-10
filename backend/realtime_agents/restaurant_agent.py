"""
Restaurant RealtimeAgent Configuration
Defines the main restaurant agent with all tools and instructions
"""

from agents.realtime import RealtimeAgent
from realtime_tools import (
    get_current_time,
    get_restaurant_hours,
    get_restaurant_location,
    get_menu_info,
    check_availability,
    make_reservation
)


def create_restaurant_agent() -> RealtimeAgent:
    """
    Create and configure the restaurant realtime agent with all tools.
    
    Returns:
        RealtimeAgent: Configured restaurant assistant agent
    """
    agent = RealtimeAgent(
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
    
    return agent


# Configuration for the RealtimeRunner
RESTAURANT_AGENT_CONFIG = {
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