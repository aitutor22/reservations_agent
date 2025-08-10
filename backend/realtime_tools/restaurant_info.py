"""
Restaurant Information Tools
Tools for providing restaurant information like hours, location, and menu
"""

from datetime import datetime
from agents import function_tool
from config import config


@function_tool
def get_current_time() -> str:
    """Get the current time."""
    current_time = datetime.now().strftime("%I:%M %p")
    return f"The current time is {current_time}"


@function_tool
def get_restaurant_hours() -> str:
    """Get the restaurant's current operating hours. Always call this when asked about opening times, closing times, or when we're open."""
    return """
    Sakura Ramen House hours:
    - Monday to Thursday: 11:30 AM - 9:30 PM
    - Friday to Saturday: 11:30 AM - 10:30 PM
    - Sunday: 11:30 AM - 9:00 PM
    """


@function_tool
def get_restaurant_location() -> str:
    """Get the restaurant's exact address and contact information. Always call this when asked about location, address, directions, or how to reach us."""
    return f"""
    Sakura Ramen House
    Address: {config.RESTAURANT_ADDRESS}
    Phone: {config.RESTAURANT_PHONE}
    
    We're located in the heart of downtown, easily accessible by public transit.
    Street parking and a public garage are available nearby.
    """


@function_tool
def get_menu_info() -> str:
    """Get detailed information about our ramen varieties, prices, and ingredients. Always call this when asked about food, menu items, or prices."""
    return """
    Our signature ramen varieties:
    
    🍜 **Tonkotsu Ramen** ($14.95)
    Rich pork bone broth simmered for 24 hours, with chashu pork, soft-boiled egg, bamboo shoots, and green onions.
    
    🍜 **Shoyu Ramen** ($13.95)
    Light soy sauce-based clear broth with chicken and vegetables, topped with chashu pork, soft-boiled egg, and nori.
    
    🍜 **Miso Ramen** ($14.95)
    Hearty miso-based broth with ground pork, corn, butter, soft-boiled egg, and green onions.
    
    🍜 **Spicy Miso Ramen** ($15.95)
    Our miso ramen with added chili oil and spices, topped with ground pork, soft-boiled egg, and green onions.
    
    🌱 **Vegetarian Ramen** ($12.95)
    Rich vegetable broth with tofu, mushrooms, corn, bamboo shoots, and seasonal vegetables.
    
    All ramen comes with handmade noodles. Extra toppings available.
    """