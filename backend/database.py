"""
Database Configuration
Async SQLAlchemy setup with PostgreSQL
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
import os
from config import config

# Database URL from environment or config
DATABASE_URL = os.getenv("DATABASE_URL", config.DATABASE_URL)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=config.DEBUG,  # Log SQL statements in debug mode
    pool_size=20,  # Number of connections to maintain in pool
    max_overflow=10,  # Maximum overflow connections
    pool_pre_ping=True,  # Test connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create declarative base for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session
    Use in FastAPI endpoints with Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database tables
    This is a simple alternative to migrations for development
    """
    async with engine.begin() as conn:
        # Import all models here to ensure they're registered
        from models.db_models import Reservation
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("Database tables created successfully")


async def close_db():
    """
    Close database connections
    Call this on application shutdown
    """
    await engine.dispose()
    print("Database connections closed")