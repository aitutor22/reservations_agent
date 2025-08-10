"""
Reservation Management Tools
Tools for checking availability and creating reservations
"""

from agents import function_tool


@function_tool
def check_availability(date: str, time: str, party_size: int) -> str:
    """
    Check if a reservation slot is available.
    
    Args:
        date: Date in format YYYY-MM-DD
        time: Time in format HH:MM
        party_size: Number of people
    """
    # TODO: Integrate with actual reservation system
    # For now, simulate availability
    import random
    
    if party_size > 8:
        return "I'm sorry, but we can only accommodate parties of up to 8 people. For larger groups, please call us directly."
    
    # Simulate availability check
    is_available = random.choice([True, True, True, False])  # 75% chance of availability
    
    if is_available:
        return f"Good news! We have availability for {party_size} people on {date} at {time}. Would you like me to make a reservation?"
    else:
        # Suggest alternative times
        alt_time1 = "6:30 PM" if "7" in time else "7:30 PM"
        alt_time2 = "8:00 PM" if "7" in time else "6:00 PM"
        return f"I'm sorry, but {time} on {date} is not available for {party_size} people. We do have availability at {alt_time1} or {alt_time2}. Would either of those work for you?"


@function_tool
def make_reservation(name: str, phone: str, date: str, time: str, party_size: int, special_requests: str = "") -> str:
    """
    Create a reservation.
    
    Args:
        name: Guest name
        phone: Contact phone number
        date: Date in format YYYY-MM-DD
        time: Time in format HH:MM
        party_size: Number of people
        special_requests: Any special requests or dietary restrictions
    """
    # TODO: Integrate with actual reservation system
    # For now, generate a confirmation number
    import random
    confirmation_number = f"SR{random.randint(10000, 99999)}"
    
    response = f"""
    ✅ Reservation confirmed!
    
    Confirmation Number: {confirmation_number}
    Name: {name}
    Date: {date}
    Time: {time}
    Party Size: {party_size}
    Phone: {phone}
    """
    
    if special_requests:
        response += f"Special Requests: {special_requests}\n"
    
    response += "\nWe've sent a confirmation to your phone. See you soon at Sakura Ramen House!"
    
    return response