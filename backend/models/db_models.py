"""
SQLAlchemy Database Models
ORM models for PostgreSQL database
"""

from sqlalchemy import Column, String, Integer, Date, Time, JSON, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from database import Base
import uuid


class Reservation(Base):
    """
    Reservation table model
    Stores restaurant reservation information
    """
    __tablename__ = "reservations"
    
    # Primary key - phone number (unique per person)
    phone_number = Column(
        String(20),
        primary_key=True,
        nullable=False,
        comment="Customer phone number in international format"
    )
    
    # Customer information
    name = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Customer name"
    )
    
    # Reservation details
    reservation_date = Column(
        Date,
        nullable=False,
        index=True,
        comment="Date of reservation"
    )
    
    reservation_time = Column(
        Time,
        nullable=False,
        comment="Time of reservation"
    )
    
    party_size = Column(
        Integer,
        nullable=False,
        comment="Number of people in the party"
    )
    
    # Additional information as JSON
    other_info = Column(
        JSON,
        nullable=True,
        default={},
        comment="Additional information (dietary restrictions, special requests, etc.)"
    )
    
    # Timestamps for audit trail
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
        comment="Last update timestamp"
    )
    
    def __repr__(self):
        return f"<Reservation(phone={self.phone_number}, name={self.name}, date={self.reservation_date} {self.reservation_time})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "phone_number": self.phone_number,
            "name": self.name,
            "reservation_date": str(self.reservation_date),
            "reservation_time": str(self.reservation_time),
            "party_size": self.party_size,
            "other_info": self.other_info,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }