"""
Main Restaurant Agent with Handoff to Reservation Specialist
Properly structured with module-level agent definitions
"""

from agents.realtime import RealtimeAgent, realtime_handoff
from realtime_tools import (
    get_current_time,
    get_restaurant_hours,
    get_restaurant_location,
    get_menu_info,
    check_availability,
    make_reservation
)

# Create the reservation specialist agent at module level
reservation_agent = RealtimeAgent(
    name="SakuraReservationSpecialist",
    instructions=(
        "You are a reservation specialist for Sakura Ramen House. "
        "You have been handed off a customer who wants to make a reservation.\n\n"
        "Your ONLY role is to:\n"
        "1. Check table availability using check_availability()\n"
        "2. Collect all necessary reservation details:\n"
        "   - Date (in YYYY-MM-DD format)\n"
        "   - Time (in HH:MM format, 24-hour)\n"
        "   - Party size (number of guests)\n"
        "   - Guest name\n"
        "   - Contact phone number\n"
        "   - Any special requests or dietary restrictions\n"
        "3. Confirm the reservation using make_reservation()\n"
        "4. Provide the confirmation number clearly\n\n"
        "IMPORTANT GUIDELINES:\n"
        "- Be efficient and focused on completing the reservation\n"
        "- Always check availability BEFORE collecting guest details\n"
        "- If the requested time is not available, offer alternatives\n"
        "- Confirm all details before finalizing the booking\n"
        "- Clearly state the confirmation number at the end\n"
        "- Thank the customer and mention we look forward to seeing them\n\n"
        "Remember: You are a specialist. Focus only on the reservation task at hand."
    ),
    tools=[
        check_availability,
        make_reservation
    ]
)

# Create the main greeting agent with handoff capability
main_agent = RealtimeAgent(
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
        realtime_handoff(reservation_agent, tool_description_override="Transfer to reservation specialist for booking tables and checking availability")
    ]
)

# Configuration for the RealtimeRunner (applies to all agents in the session)
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