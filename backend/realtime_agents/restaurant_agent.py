"""
Restaurant RealtimeAgent Configuration
Main greeting agent with handoff capability to specialized agents
"""

from agents.realtime import RealtimeAgent, realtime_handoff
from realtime_tools import (
    get_current_time,
    get_restaurant_hours,
    get_restaurant_location,
    get_menu_info
)
from .reservation_agent import create_reservation_agent


def create_restaurant_agent() -> RealtimeAgent:
    """
    Create the main greeting agent with handoff capability to reservation specialist.
    
    Returns:
        RealtimeAgent: Configured main restaurant agent with handoff
    """
    # Create the reservation specialist that we'll hand off to
    reservation_agent = create_reservation_agent()
    
    # BEST PRACTICE: Agent instructions should include both high-level guidance AND specific tool usage.
    # This "controlled redundancy" pattern is recommended by OpenAI because:
    # 1. Agent instructions provide strategic context and behavioral guidelines
    # 2. Tool docstrings provide tactical function-level documentation
    # 3. Explicit tool mentions in instructions reduce hallucination and improve tool usage
    # 4. The redundancy acts as reinforcement, making the agent more reliable
    agent = RealtimeAgent(
        name="SakuraRamenAssistant",
        instructions=(
            "You are a friendly and welcoming voice assistant for Sakura Ramen House, "
            "a popular Japanese ramen restaurant located at 78 Boat Quay, Singapore 049866. "
            "Our phone number is +65 6877 9888.\n\n"
            "Your primary role is to:\n"
            "1. Warmly greet customers and make them feel welcome\n"
            "2. Answer questions about our restaurant (hours, location, menu)\n"
            "3. Provide information about our delicious ramen varieties\n\n"
            "IMPORTANT HANDOFF INSTRUCTION:\n"
            "When a customer expresses intent to make a reservation, book a table, or asks about availability, "
            "you should IMMEDIATELY transfer them to the reservation specialist by using the handoff tool. "
            "Say something like: 'I'll connect you with our reservation specialist who can help you book a table.'\n\n"
            "Use the provided tools to get accurate information:\n"
            "- Use get_restaurant_location() for address and contact details\n"
            "- Use get_restaurant_hours() for operating hours\n"
            "- Use get_menu_info() for menu details and prices\n\n"
            "Keep responses conversational, warm, and enthusiastic about our food. "
            "Be helpful and engaging, but remember to hand off reservation requests promptly."
        ),
        tools=[
            get_current_time,
            get_restaurant_hours,
            get_restaurant_location,
            get_menu_info
        ],
        handoffs=[
            realtime_handoff(
                reservation_agent,
                tool_description="Transfer to reservation specialist for booking tables and checking availability"
            )
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