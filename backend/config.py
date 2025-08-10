"""
Configuration settings for the Restaurant Voice Reservation Agent
"""

import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Vector Store Configuration
    VECTOR_STORE_ID: Optional[str] = os.getenv("VECTOR_STORE_ID")
    VECTOR_STORE_NAME: str = "Sakura Ramen House Knowledge Base"
    
    # FastAPI Configuration
    APP_NAME: str = "Restaurant Voice Reservation Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # WebSocket Configuration
    WS_HEARTBEAT_INTERVAL: int = 30  # seconds
    WS_CONNECTION_TIMEOUT: int = 60  # seconds
    
    # CORS Configuration
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",  # Vue CLI default port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",  # Vue CLI default port
    ]
    
    # Session Configuration
    SESSION_TIMEOUT: int = 300  # 5 minutes in seconds
    MAX_SESSIONS: int = 100
    
    # Audio Configuration
    AUDIO_SAMPLE_RATE: int = 24000
    AUDIO_CHANNELS: int = 1
    AUDIO_CHUNK_SIZE: int = 1024
    
    # Restaurant-specific Configuration
    RESTAURANT_NAME: str = "Sakura Ramen House"
    RESTAURANT_PHONE: str = "+65 6877 9888"
    RESTAURANT_ADDRESS: str = "78 Boat Quay, Singapore 049866"
    
    # Agent Configuration
    KNOWLEDGE_AGENT_INSTRUCTIONS: str = (
        "You answer questions about Sakura Ramen House with accurate, concise responses. "
        "Use the restaurant knowledge base to provide information about menu, hours, location, "
        "wait times, and policies. Be helpful and friendly."
    )
    
    RESERVATION_AGENT_INSTRUCTIONS: str = (
        "You help customers make reservations at Sakura Ramen House. "
        "Note: The restaurant operates on a walk-in basis only, no reservations accepted. "
        "Inform customers about the digital queue system and typical wait times."
    )
    
    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/reservations"
    )
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "20"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
    DATABASE_POOL_RECYCLE: int = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))
    
    # File paths
    BASE_DIR: Path = Path(__file__).parent
    KNOWLEDGE_DIR: Path = BASE_DIR / "knowledge"
    CONFIG_DIR: Path = BASE_DIR / "config"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required. Set it in .env file or environment variables.")
        
        return True
    
    @classmethod
    def get_vector_store_config(cls) -> dict:
        """Get vector store configuration"""
        import json
        
        vector_store_config_file = cls.CONFIG_DIR / "vector_store.json"
        
        if vector_store_config_file.exists():
            with open(vector_store_config_file, 'r') as f:
                return json.load(f)
        
        return {
            "vector_store_id": cls.VECTOR_STORE_ID,
            "vector_store_name": cls.VECTOR_STORE_NAME
        }


# Create a singleton instance
config = Config()