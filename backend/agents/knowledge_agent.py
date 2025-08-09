"""
Knowledge Agent for Restaurant Information
Handles queries about menu, hours, location, and general restaurant information
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


class KnowledgeAgent:
    """Agent that answers questions about the restaurant using vector store search"""
    
    def __init__(self, api_key: Optional[str] = None, vector_store_id: Optional[str] = None):
        """Initialize the Knowledge Agent with OpenAI client and vector store"""
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
        
        # Create the assistant
        self._create_assistant()
    
    def _create_assistant(self):
        """Create the OpenAI Assistant with FileSearch tool"""
        try:
            self.assistant = self.client.beta.assistants.create(
                name="Sakura Ramen House Knowledge Agent",
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
            print(f"Knowledge Agent created with ID: {self.assistant.id}")
        except Exception as e:
            print(f"Error creating Knowledge Agent: {e}")
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
            # Use provided thread or create new one
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
def test_knowledge_agent():
    """Test the Knowledge Agent with sample queries"""
    agent = KnowledgeAgent()
    
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
    
    print("Testing Knowledge Agent with sample queries...\n")
    
    for query in test_queries:
        print(f"Q: {query}")
        result = agent.process_query(query)
        
        if result["success"]:
            print(f"A: {result['response']}\n")
        else:
            print(f"Error: {result['error']}\n")
    
    # Clean up
    agent.cleanup()


if __name__ == "__main__":
    # Run test if executed directly
    import sys
    
    if "--test" in sys.argv:
        test_knowledge_agent()
    else:
        print("Knowledge Agent module loaded. Use --test flag to run tests.")