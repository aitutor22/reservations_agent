#!/usr/bin/env python3
"""
Test script to verify voice personality is being loaded correctly
Run this to check if the personality configuration is working
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_personality_loading():
    print("\n" + "="*70)
    print("VOICE PERSONALITY TEST SCRIPT")
    print("="*70)
    
    # Import after path is set
    from realtime_agents.voice_personality import (
        BASE_PERSONALITY, 
        TEST_MODE,
        get_agent_instructions
    )
    
    print(f"\n1. TEST MODE STATUS: {'ACTIVE' if TEST_MODE else 'DISABLED'}")
    print("-"*70)
    
    if TEST_MODE:
        print("✅ Test mode is ACTIVE - you should hear exaggerated Singaporean accent")
        print("   Expected phrases:")
        print("   - 'Personality test mode active!' at start of responses")
        print("   - Frequent use of 'lah', 'wah', 'shiok'")
        print("   - 'Can can' for agreement")
    else:
        print("❌ Test mode is DISABLED - using production personality")
        print("   To enable test mode, set TEST_MODE = True in voice_personality.py")
    
    print("\n2. PERSONALITY CONTENT CHECK")
    print("-"*70)
    
    # Check what's in the base personality
    test_markers = [
        ("TEST MODE", "Test mode marker"),
        ("25 year old female", "Age and gender"),
        ("Singaporean", "Singaporean accent"),
        ("lah", "Singlish marker 'lah'"),
        ("shiok", "Singlish word 'shiok'"),
        ("omotenashi", "Japanese hospitality"),
        ("Boat Quay", "Singapore location")
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
        
        # Check if test mode personality is in main agent
        if "TEST MODE" in main_agent.instructions:
            print("\n   ✅ TEST PERSONALITY IS ACTIVE IN AGENTS")
        else:
            print("\n   ❌ Test personality NOT found in agents")
            
    except Exception as e:
        print(f"   ❌ Error loading agents: {e}")
    
    print("\n5. RECOMMENDATIONS")
    print("-"*70)
    
    if TEST_MODE:
        print("   1. Start the server with: uvicorn main:app --reload")
        print("   2. Test with these phrases:")
        print("      - 'Hello' → Should hear 'Wah, hello! Welcome to Sakura Ramen House lah!'")
        print("      - 'What's good?' → Should hear 'shiok' and 'confirm'")
        print("      - 'What time?' → Should mention Singapore time")
        print("   3. If you DON'T hear these markers, the personality isn't loading")
    else:
        print("   1. Enable test mode: Set TEST_MODE = True in voice_personality.py")
        print("   2. Re-run this script")
        print("   3. Restart the server")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    test_personality_loading()