"""
Vector Store Manager for Restaurant Knowledge Base
Handles creation and management of OpenAI vector stores for the knowledge agent
"""

import os
import json
from typing import Optional, Dict, Any
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class VectorStoreManager:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Vector Store Manager with OpenAI client"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.config_file = Path(__file__).parent.parent / "config" / "vector_store.json"
        self.config_file.parent.mkdir(exist_ok=True)
        
    def _load_config(self) -> Dict[str, Any]:
        """Load vector store configuration from file"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save vector store configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def create_vector_store(self, store_name: str = "Ichiban Ramen House Knowledge Base") -> Dict[str, Any]:
        """Create a new vector store for the restaurant knowledge base"""
        try:
            vector_store = self.client.beta.vector_stores.create(name=store_name)
            
            details = {
                "id": vector_store.id,
                "name": vector_store.name,
                "created_at": vector_store.created_at,
                "file_count": vector_store.file_counts.completed
            }
            
            # Save the vector store ID to config
            config = self._load_config()
            config["vector_store_id"] = vector_store.id
            config["vector_store_name"] = vector_store.name
            self._save_config(config)
            
            print(f"Vector store created successfully: {details}")
            return details
            
        except Exception as e:
            print(f"Error creating vector store: {e}")
            raise
    
    def upload_file_to_store(self, file_path: str, vector_store_id: Optional[str] = None) -> Dict[str, Any]:
        """Upload a file to the vector store"""
        # Use provided vector_store_id or get from config
        if not vector_store_id:
            config = self._load_config()
            vector_store_id = config.get("vector_store_id")
            
        if not vector_store_id:
            raise ValueError("No vector store ID provided and none found in config. Create a vector store first.")
        
        file_name = os.path.basename(file_path)
        
        try:
            # Upload file to OpenAI
            with open(file_path, 'rb') as file:
                file_response = self.client.files.create(
                    file=file,
                    purpose="assistants"
                )
            
            # Attach file to vector store
            attach_response = self.client.beta.vector_stores.files.create(
                vector_store_id=vector_store_id,
                file_id=file_response.id
            )
            
            result = {
                "file": file_name,
                "file_id": file_response.id,
                "vector_store_id": vector_store_id,
                "status": "success"
            }
            
            print(f"File '{file_name}' uploaded successfully to vector store")
            return result
            
        except Exception as e:
            print(f"Error uploading file '{file_name}': {str(e)}")
            return {
                "file": file_name,
                "status": "failed",
                "error": str(e)
            }
    
    def get_or_create_vector_store(self, store_name: str = "Ichiban Ramen House Knowledge Base") -> str:
        """Get existing vector store ID from config or create a new one"""
        config = self._load_config()
        vector_store_id = config.get("vector_store_id")
        
        if vector_store_id:
            # Verify the vector store still exists
            try:
                vector_store = self.client.beta.vector_stores.retrieve(vector_store_id)
                print(f"Using existing vector store: {vector_store_id}")
                return vector_store_id
            except Exception as e:
                print(f"Existing vector store not found: {e}")
                print("Creating new vector store...")
        
        # Create new vector store
        details = self.create_vector_store(store_name)
        return details["id"]
    
    def initialize_knowledge_base(self) -> str:
        """Initialize the knowledge base with restaurant information"""
        # Get or create vector store
        vector_store_id = self.get_or_create_vector_store()
        
        # Upload restaurant info file
        knowledge_file = Path(__file__).parent / "restaurant_info.md"
        
        if knowledge_file.exists():
            self.upload_file_to_store(str(knowledge_file), vector_store_id)
        else:
            print(f"Warning: Knowledge file not found at {knowledge_file}")
        
        return vector_store_id
    
    def list_vector_store_files(self, vector_store_id: Optional[str] = None) -> list:
        """List all files in the vector store"""
        if not vector_store_id:
            config = self._load_config()
            vector_store_id = config.get("vector_store_id")
            
        if not vector_store_id:
            raise ValueError("No vector store ID provided and none found in config.")
        
        try:
            files = self.client.beta.vector_stores.files.list(
                vector_store_id=vector_store_id
            )
            
            file_list = []
            for file in files.data:
                file_list.append({
                    "id": file.id,
                    "created_at": file.created_at,
                    "status": file.status
                })
            
            return file_list
            
        except Exception as e:
            print(f"Error listing vector store files: {e}")
            return []


# Utility function for quick initialization
def setup_knowledge_base(api_key: Optional[str] = None) -> str:
    """Quick setup function to initialize the entire knowledge base"""
    manager = VectorStoreManager(api_key)
    vector_store_id = manager.initialize_knowledge_base()
    print(f"Knowledge base initialized with vector store ID: {vector_store_id}")
    return vector_store_id


if __name__ == "__main__":
    # Example usage - initialize the knowledge base
    try:
        vector_store_id = setup_knowledge_base()
        print(f"Setup complete! Vector store ID: {vector_store_id}")
    except Exception as e:
        print(f"Setup failed: {e}")