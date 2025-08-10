#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick test to verify agents import correctly with the lookup tool
"""

import sys
import os
# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realtime_agents import main_agent, reservation_agent

print("✅ Imports successful")
print(f"Main agent name: {main_agent.name}")
print(f"Reservation agent name: {reservation_agent.name}")
print(f"Reservation agent has {len(reservation_agent.tools)} tools:")
for tool in reservation_agent.tools:
    print(f"  - {tool.name}")

# Test that the lookup tool exists
from realtime_tools import lookup_reservation
print("\n✅ lookup_reservation tool imported successfully")

# Test the phone formatting
from realtime_tools.api_client import format_phone_number
test_phone = "98207272"
formatted = format_phone_number(test_phone)
print(f"\nPhone formatting test:")
print(f"  Input: {test_phone}")
print(f"  Output: {formatted}")
assert formatted == "+6598207272", "Phone formatting failed"
print("  ✅ Phone formatting working")

print("\n✅ All tests passed!")