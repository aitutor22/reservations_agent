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
    # BEST PRACTICE: Agent instructions should include both high-level guidance AND specific tool usage.
    # This "controlled redundancy" pattern is recommended by OpenAI because:
    # 1. Agent instructions provide strategic context and behavioral guidelines
    # 2. Tool docstrings provide tactical function-level documentation
    # 3. Explicit tool mentions in instructions reduce hallucination and improve tool usage
    # 4. The redundancy acts as reinforcement, making the agent more reliable
    # Even though tool docstrings describe when to use each tool, explicitly mentioning them
    # in the agent instructions significantly improves the agent's likelihood of using tools
    # rather than hallucinating answers from general knowledge.
    agent = RealtimeAgent(
        name="SakuraRamenAssistant",
        instructions=(
            "You are a friendly and helpful voice assistant for Sakura Ramen House, "
            "a popular Japanese ramen restaurant located at 78 Boat Quay, Singapore 049866. "
            "Our phone number is +65 6877 9888.\n\n"
            "Your role is to:\n"
            "1. Answer questions about our restaurant (hours, location, menu)\n"
            "2. Check availability for reservations\n"
            "3. Make reservations for guests\n"
            "4. Provide information about our delicious ramen varieties\n\n"
            "IMPORTANT: Always use the provided tools to get accurate, up-to-date information:\n"
            "- Use get_restaurant_location() for address and contact details\n"
            "- Use get_restaurant_hours() for operating hours\n"
            "- Use get_menu_info() for menu details and prices\n"
            "- Use check_availability() before confirming any reservation\n\n"
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