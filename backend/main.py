"""
FastAPI Main Application
Restaurant Voice Reservation Agent Backend
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import config
from knowledge.vector_store_manager import setup_knowledge_base
from database import init_db, close_db

# Import routers
from api.routes import reservations
from api.websockets import realtime_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    print("Starting Restaurant Voice Reservation Agent...")
    
    # Initialize database
    try:
        await init_db()
    except Exception as db_error:
        print(f"Warning: Could not initialize database: {db_error}")
        print("Continuing without database support...")
    
    # Initialize knowledge base
    print("Initializing knowledge base...")
    try:
        vector_store_id = setup_knowledge_base()
        print(f"Knowledge base ready with vector store: {vector_store_id}")
    except Exception as kb_error:
        print(f"Warning: Could not initialize knowledge base: {kb_error}")
        print("Continuing without vector store support...")
    
    yield
    
    # Shutdown
    print("Shutting down...")
    
    # Close database connections
    await close_db()
    
    print("Cleanup complete")


# Create FastAPI app
app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(reservations.router)
app.include_router(realtime_agent.router)
