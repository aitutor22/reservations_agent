"""
OpenAI Service
Handles OpenAI Realtime API integration and agent orchestration
"""

import asyncio
from typing import Optional, Dict, Any, Tuple
from enum import Enum
import re
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from agents.knowledge_agent import KnowledgeAgent


class AgentState(Enum):
    """Enumeration of agent states"""
    GREETING = "greeting"
    KNOWLEDGE = "knowledge"
    RESERVATION = "reservation"
    CONFIRMATION = "confirmation"


class IntentClassifier:
    """Classify user intent to route to appropriate agent"""
    
    # Keywords for different intents
    RESERVATION_KEYWORDS = [
        "reservation", "book", "table", "reserve", "booking",
        "appointment", "schedule", "available", "party of"
    ]
    
    KNOWLEDGE_KEYWORDS = [
        "menu", "hours", "open", "close", "location", "where",
        "address", "parking", "wait", "time", "price", "cost",
        "vegetarian", "vegan", "gluten", "allergy", "dish",
        "ramen", "beer", "sake", "drink", "food", "special"
    ]
    
    @classmethod
    def classify_intent(cls, text: str) -> str:
        """Classify the intent of user input"""
        text_lower = text.lower()
        
        # Check for reservation intent
        for keyword in cls.RESERVATION_KEYWORDS:
            if keyword in text_lower:
                return AgentState.RESERVATION.value
        
        # Check for knowledge intent
        for keyword in cls.KNOWLEDGE_KEYWORDS:
            if keyword in text_lower:
                return AgentState.KNOWLEDGE.value
        
        # Default to knowledge for general questions
        if "?" in text:
            return AgentState.KNOWLEDGE.value
        
        # Default to greeting for unclear intent
        return AgentState.GREETING.value


class OpenAIService:
    """Service to handle OpenAI API interactions and agent orchestration"""
    
    def __init__(self):
        """Initialize the OpenAI service with agents"""
        # Validate configuration
        config.validate()
        
        # Initialize agents
        self.knowledge_agent: Optional[KnowledgeAgent] = None
        self.current_state = AgentState.GREETING
        self.session_context: Dict[str, Any] = {}
        
        # Initialize the knowledge agent
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all agent instances"""
        try:
            # Initialize Knowledge Agent
            self.knowledge_agent = KnowledgeAgent()
            print("Knowledge Agent initialized successfully")
            
            # TODO: Initialize Reservation Agent when implemented
            # self.reservation_agent = ReservationAgent()
            
        except Exception as e:
            print(f"Error initializing agents: {e}")
            raise
    
    async def process_greeting(self, user_input: str) -> Tuple[str, str]:
        """Process initial greeting and route to appropriate agent"""
        # Classify intent
        intent = IntentClassifier.classify_intent(user_input)
        
        if intent == AgentState.RESERVATION.value:
            self.current_state = AgentState.RESERVATION
            response = (
                "I understand you'd like to make a reservation. "
                "I should mention that Sakura Ramen House operates on a walk-in basis only - "
                "we don't accept reservations. However, we have a digital queue system "
                "that lets you join the waitlist and receive an SMS when your table is ready. "
                "Would you like to know more about our typical wait times?"
            )
        elif intent == AgentState.KNOWLEDGE.value:
            self.current_state = AgentState.KNOWLEDGE
            # Process with knowledge agent
            result = self.knowledge_agent.process_query(user_input)
            if result["success"]:
                response = result["response"]
            else:
                response = "I'm here to help! What would you like to know about Sakura Ramen House?"
        else:
            response = (
                "Welcome to Sakura Ramen House! I'm your virtual assistant. "
                "I can help you with information about our menu, hours, location, "
                "or explain our walk-in queue system. What would you like to know?"
            )
        
        return response, self.current_state.value
    
    async def process_message(self, user_input: str, state: Optional[str] = None) -> Tuple[str, str]:
        """Process a message based on current agent state"""
        # Update state if provided
        if state:
            self.current_state = AgentState(state)
        
        # Route based on current state
        if self.current_state == AgentState.GREETING:
            return await self.process_greeting(user_input)
        
        elif self.current_state == AgentState.KNOWLEDGE:
            result = self.knowledge_agent.process_query(user_input)
            if result["success"]:
                response = result["response"]
            else:
                response = f"I apologize, I couldn't find that information. Please try asking in a different way."
            
            # Check if user wants to switch context
            if "reservation" in user_input.lower() or "book" in user_input.lower():
                self.current_state = AgentState.RESERVATION
                response += (
                    "\n\nI noticed you mentioned reservations. Just to remind you, "
                    "we operate on a walk-in basis with a digital queue system."
                )
            
            return response, self.current_state.value
        
        elif self.current_state == AgentState.RESERVATION:
            # TODO: Implement reservation agent logic
            response = (
                "Our restaurant operates on a walk-in basis only. "
                "Here are our typical wait times:\n"
                "- Weekday Lunch: 30-45 minutes\n"
                "- Weekday Dinner: 20-30 minutes\n"
                "- Friday/Saturday Dinner: 45-60 minutes\n"
                "- Weekends: 30-60 minutes\n\n"
                "We have a digital queue system that sends SMS notifications. "
                "Would you like to know the best times to visit for shorter waits?"
            )
            return response, self.current_state.value
        
        else:
            # Default fallback
            return await self.process_greeting(user_input)
    
    def get_session_context(self) -> Dict[str, Any]:
        """Get the current session context"""
        return {
            "state": self.current_state.value,
            "context": self.session_context,
            "thread_id": self.knowledge_agent.thread_id if self.knowledge_agent else None
        }
    
    def reset_session(self):
        """Reset the session to initial state"""
        self.current_state = AgentState.GREETING
        self.session_context = {}
        
        if self.knowledge_agent:
            self.knowledge_agent.clear_thread()
    
    def cleanup(self):
        """Clean up resources"""
        if self.knowledge_agent:
            self.knowledge_agent.cleanup()


# Singleton instance
_service_instance: Optional[OpenAIService] = None


def get_openai_service() -> OpenAIService:
    """Get or create the OpenAI service singleton"""
    global _service_instance
    if not _service_instance:
        _service_instance = OpenAIService()
    return _service_instance


# Example usage
async def test_service():
    """Test the OpenAI service"""
    service = get_openai_service()
    
    test_messages = [
        "Hello!",
        "What are your hours?",
        "What's the most popular ramen?",
        "I'd like to make a reservation",
        "What are the wait times on Friday night?"
    ]
    
    print("Testing OpenAI Service with sample messages...\n")
    
    for msg in test_messages:
        print(f"User: {msg}")
        response, state = await service.process_message(msg)
        print(f"Agent ({state}): {response}\n")
    
    service.cleanup()


if __name__ == "__main__":
    # Run test if executed directly
    import sys
    
    if "--test" in sys.argv:
        asyncio.run(test_service())
    else:
        print("OpenAI Service module loaded. Use --test flag to run tests.")