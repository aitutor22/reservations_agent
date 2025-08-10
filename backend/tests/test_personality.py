#!/usr/bin/env python3
"""
Test script to verify voice personality is being loaded correctly
Run this to check if the personality configuration is working
"""

import sys
import os
# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_personality_loading():
    print("\n" + "="*70)
    print("VOICE PERSONALITY TEST SCRIPT")
    print("="*70)
    
    # Import after path is set
    from realtime_agents.voice_personality import (
        BASE_PERSONALITY, 
        get_agent_instructions
    )
    
    print(f"\n1. PERSONALITY TYPE")
    print("-"*70)
    print("✅ Using production personality configuration")
    print("   - Professional Japanese restaurant receptionist")
    print("   - Clear Singaporean accent")
    print("   - Polite and formal with friendly warmth")
    
    print("\n2. PERSONALITY CONTENT CHECK")
    print("-"*70)
    
    # Check what's in the base personality
    test_markers = [
        ("Japanese restaurant receptionist", "Role description"),
        ("Singaporean accent", "Accent type"),
        ("Professional", "Professional demeanor"),
        ("respectful", "Respectful tone"),
        ("Sakura Ramen House", "Restaurant name")
    ]
    
    for marker, description in test_markers:
        present = marker in BASE_PERSONALITY
        symbol = "✅" if present else "❌"
        print(f"   {symbol} {description}: {marker}")
    
    print("\n3. AGENT INSTRUCTIONS LENGTH")
    print("-"*70)
    
    roles = ["main", "information", "reservation"]
    for role in roles:
        instructions = get_agent_instructions(role)
        print(f"   {role.capitalize()} agent: {len(instructions)} characters")
        
    print("\n4. TESTING WITH MAIN_AGENT MODULE")
    print("-"*70)
    
    try:
        from realtime_agents.main_agent import main_agent, information_agent, reservation_agent, RESTAURANT_AGENT_CONFIG
        
        print(f"   Main agent loaded: {len(main_agent.instructions)} chars")
        print(f"   Info agent loaded: {len(information_agent.instructions)} chars")
        print(f"   Reservation agent loaded: {len(reservation_agent.instructions)} chars")
        print(f"   Voice configured: {RESTAURANT_AGENT_CONFIG['model_settings']['voice']}")
        
        # Check if personality is loaded in main agent
        if "Japanese restaurant receptionist" in main_agent.instructions:
            print("\n   ✅ Personality loaded correctly in agents")
        else:
            print("\n   ❌ Personality not found in agents")
            
    except Exception as e:
        print(f"   ❌ Error loading agents: {e}")
    
    print("\n5. RECOMMENDATIONS")
    print("-"*70)
    
    print("   1. Start the server with: uvicorn main:app --reload")
    print("   2. Test with these phrases:")
    print("      - 'Hello' → Should hear professional greeting")
    print("      - 'I want to check my reservation' → Should offer to help lookup")
    print("      - 'I want to make a reservation' → Should check availability")
    print("   3. To modify personality, edit voice_personality.py")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    test_personality_loading()