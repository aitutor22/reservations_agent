"""
Reservation Agent
Specialized agent that only handles reservation-related tasks
"""

from agents.realtime import RealtimeAgent
from .voice_personality import get_agent_instructions
from realtime_tools import (
    check_availability,
    make_reservation
)


def create_reservation_agent() -> RealtimeAgent:
    """
    Create a specialized reservation agent that focuses only on booking tables.
    
    Returns:
        RealtimeAgent: Configured reservation specialist agent
    """
    agent = RealtimeAgent(
        name="SakuraReservationSpecialist",
        instructions=get_agent_instructions("reservation") + """
        
You have been handed off a customer who wants to make a reservation.

Your ONLY role is to:
1. Check table availability using check_availability()
2. Collect all necessary reservation details:
   - Date (in YYYY-MM-DD format)
   - Time (in HH:MM format, 24-hour)
   - Party size (number of guests)
   - Guest name
   - Contact phone number
   - Any special requests or dietary restrictions
3. Confirm the reservation using make_reservation()
4. Provide the confirmation number clearly

IMPORTANT GUIDELINES:
- Be efficient and focused on completing the reservation
- Always check availability BEFORE collecting guest details
- If the requested time is not available, offer alternatives
- Confirm all details before finalizing the booking
- Clearly state the confirmation number at the end
- Thank the customer and mention we look forward to seeing them

Remember: You are a specialist. Focus only on the reservation task at hand.
        """,
        tools=[
            check_availability,
            make_reservation
        ]
    )
    
    return agent