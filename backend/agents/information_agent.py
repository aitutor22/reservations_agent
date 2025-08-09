"""
Information Agent for Restaurant Information
Handles all restaurant information queries including menu, hours, location, 
specials, policies, and general restaurant information. 

This agent combines both simple quick responses for basic info and 
vector store search for complex queries.
"""

from typing import Optional, Dict, Any, List
from openai import OpenAI
from openai.types.beta import Assistant
from openai.types.beta.threads import Message
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from knowledge.vector_store_manager import VectorStoreManager


class InformationAgent:
    """
    Agent that answers all restaurant information questions.
    Handles both simple quick responses and complex queries using vector store search.
    """
    
    def __init__(self, api_key: Optional[str] = None, vector_store_id: Optional[str] = None):
        """Initialize the Information Agent with OpenAI client and vector store"""
        self.api_key = api_key or config.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # Get or create vector store
        if not vector_store_id:
            # Try to get from config
            store_config = config.get_vector_store_config()
            vector_store_id = store_config.get("vector_store_id")
            
            # If still no ID, initialize the knowledge base
            if not vector_store_id:
                print("No vector store found. Initializing knowledge base...")
                manager = VectorStoreManager(self.api_key)
                vector_store_id = manager.initialize_knowledge_base()
        
        self.vector_store_id = vector_store_id
        self.assistant: Optional[Assistant] = None
        self.thread_id: Optional[str] = None
        
        # Quick responses for basic info
        self._init_quick_responses()
        
        # Create the assistant
        self._create_assistant()
    
    def _init_quick_responses(self):
        """Initialize quick responses for common basic queries"""
        self.quick_responses = {
            "hours": {
                "keywords": ["hours", "open", "close", "operating", "time", "when"],
                "response": f"{config.RESTAURANT_NAME} is open daily from 11:30 AM to 10:00 PM (last order at 9:30 PM). We're closed on Mondays for maintenance."
            },
            "location": {
                "keywords": ["location", "address", "where", "directions", "how to get"],
                "response": f"We're located at {config.RESTAURANT_ADDRESS}. We're right by the Singapore River with easy access via Clarke Quay MRT station."
            },
            "phone": {
                "keywords": ["phone", "number", "call", "contact"],
                "response": f"You can reach us at {config.RESTAURANT_PHONE}. However, we operate on a walk-in basis and don't take reservations over the phone."
            },
            "reservations": {
                "keywords": ["reservation", "book", "booking", "table"],
                "response": "We operate on a walk-in basis only. However, you can join our digital queue system when you arrive to minimize your wait time!"
            }
        }
    
    def _get_quick_response(self, query: str) -> Optional[str]:
        """Check if query matches a quick response pattern"""
        query_lower = query.lower()
        
        for response_type, data in self.quick_responses.items():
            if any(keyword in query_lower for keyword in data["keywords"]):
                return data["response"]
        
        return None
    
    def _create_assistant(self):
        """Create the OpenAI Assistant with FileSearch tool"""
        try:
            self.assistant = self.client.beta.assistants.create(
                name="Sakura Ramen House Information Agent",
                instructions=config.KNOWLEDGE_AGENT_INSTRUCTIONS,
                model=config.OPENAI_MODEL,
                tools=[{
                    "type": "file_search",
                    "file_search": {
                        "max_num_results": 3
                    }
                }],
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [self.vector_store_id]
                    }
                }
            )
            print(f"Information Agent created with ID: {self.assistant.id}")
        except Exception as e:
            print(f"Error creating Information Agent: {e}")
            raise
    
    def create_thread(self) -> str:
        """Create a new conversation thread"""
        try:
            thread = self.client.beta.threads.create()
            self.thread_id = thread.id
            return thread.id
        except Exception as e:
            print(f"Error creating thread: {e}")
            raise
    
    def process_query(self, query: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """Process a user query and return the response"""
        try:
            # Check for quick responses first
            quick_response = self._get_quick_response(query)
            if quick_response:
                return {
                    "success": True,
                    "response": quick_response,
                    "source": "quick_response",
                    "thread_id": self.thread_id
                }
            
            # Use provided thread or create new one for complex queries
            if thread_id:
                self.thread_id = thread_id
            elif not self.thread_id:
                self.create_thread()
            
            # Add message to thread
            message = self.client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role="user",
                content=query
            )
            
            # Run the assistant
            run = self.client.beta.threads.runs.create(
                thread_id=self.thread_id,
                assistant_id=self.assistant.id
            )
            
            # Wait for completion
            while run.status not in ["completed", "failed", "cancelled", "expired"]:
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread_id,
                    run_id=run.id
                )
            
            if run.status != "completed":
                return {
                    "success": False,
                    "error": f"Run failed with status: {run.status}",
                    "response": None
                }
            
            # Get the response
            messages = self.client.beta.threads.messages.list(
                thread_id=self.thread_id,
                order="desc",
                limit=1
            )
            
            if messages.data:
                response_content = messages.data[0].content[0].text.value
                return {
                    "success": True,
                    "response": response_content,
                    "source": "vector_search",
                    "thread_id": self.thread_id
                }
            else:
                return {
                    "success": False,
                    "error": "No response generated",
                    "response": None
                }
                
        except Exception as e:
            print(f"Error processing query: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": None
            }
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the conversation history from the current thread"""
        if not self.thread_id:
            return []
        
        try:
            messages = self.client.beta.threads.messages.list(
                thread_id=self.thread_id,
                order="asc"
            )
            
            history = []
            for msg in messages.data:
                history.append({
                    "role": msg.role,
                    "content": msg.content[0].text.value,
                    "timestamp": msg.created_at
                })
            
            return history
            
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return []
    
    def clear_thread(self):
        """Clear the current thread (start new conversation)"""
        self.thread_id = None
    
    def cleanup(self):
        """Clean up resources (delete assistant if needed)"""
        if self.assistant:
            try:
                self.client.beta.assistants.delete(self.assistant.id)
                print(f"Deleted assistant: {self.assistant.id}")
            except Exception as e:
                print(f"Error deleting assistant: {e}")


# Example usage and testing
def test_information_agent():
    """Test the Information Agent with sample queries"""
    agent = InformationAgent()
    
    # Test queries
    test_queries = [
        "What are your operating hours?",
        "What's on the menu?",
        "How long is the wait time on Friday nights?",
        "Do you take reservations?",
        "Where are you located?",
        "What's the most popular ramen?",
        "Do you have vegetarian options?"
    ]
    
    print("Testing Information Agent with sample queries...\n")
    
    for query in test_queries:
        print(f"Q: {query}")
        result = agent.process_query(query)
        
        if result["success"]:
            source = result.get('source', 'unknown')
            print(f"A ({source}): {result['response']}\n")
        else:
            print(f"Error: {result['error']}\n")
    
    # Clean up
    agent.cleanup()


if __name__ == "__main__":
    # Run test if executed directly
    import sys
    
    if "--test" in sys.argv:
        test_information_agent()
    else:
        print("Information Agent module loaded. Use --test flag to run tests.")