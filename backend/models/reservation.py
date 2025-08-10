"""
Reservation Models
Pydantic models for reservation data validation and serialization
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime, date, time
import re


class ReservationBase(BaseModel):
    """Base reservation model with common fields"""
    phone_number: str = Field(
        ...,
        description="Customer phone number (e.g., +6598207272)",
        example="+6598207272"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Customer name",
        example="John Doe"
    )
    reservation_date: str = Field(
        ...,
        description="Reservation date in ISO format (YYYY-MM-DD)",
        example="2024-03-15"
    )
    reservation_time: str = Field(
        ...,
        description="Reservation time in HH:MM format",
        example="19:30"
    )
    party_size: int = Field(
        ...,
        ge=1,
        le=20,
        description="Number of people in the party",
        example=4
    )
    other_info: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional information (dietary restrictions, special requests, etc.)",
        example={"dietary_restrictions": ["vegetarian"], "special_request": "Birthday celebration"}
    )
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        """Validate phone number format"""
        # Simple validation for international format
        # Accepts + followed by country code and number
        pattern = r'^\+\d{7,15}$'
        if not re.match(pattern, v):
            raise ValueError(
                'Phone number must be in international format (e.g., +6598207272)'
            )
        return v
    
    @validator('reservation_date')
    def validate_date(cls, v):
        """Validate date format"""
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError('Date must be in ISO format (YYYY-MM-DD)')
        return v
    
    @validator('reservation_time')
    def validate_time(cls, v):
        """Validate time format"""
        try:
            time.fromisoformat(v)
        except ValueError:
            raise ValueError('Time must be in HH:MM format')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone_number": "+6598207272",
                "name": "John Doe",
                "reservation_date": "2024-03-15",
                "reservation_time": "19:30",
                "party_size": 4,
                "other_info": {
                    "dietary_restrictions": ["vegetarian"],
                    "special_request": "Birthday celebration"
                }
            }
        }


class ReservationCreate(ReservationBase):
    """Model for creating a new reservation"""
    pass


class ReservationUpdate(BaseModel):
    """Model for updating an existing reservation"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    reservation_date: Optional[str] = None
    reservation_time: Optional[str] = None
    party_size: Optional[int] = Field(None, ge=1, le=20)
    other_info: Optional[Dict[str, Any]] = None
    
    @validator('reservation_date')
    def validate_date(cls, v):
        """Validate date format if provided"""
        if v is not None:
            try:
                date.fromisoformat(v)
            except ValueError:
                raise ValueError('Date must be in ISO format (YYYY-MM-DD)')
        return v
    
    @validator('reservation_time')
    def validate_time(cls, v):
        """Validate time format if provided"""
        if v is not None:
            try:
                time.fromisoformat(v)
            except ValueError:
                raise ValueError('Time must be in HH:MM format')
        return v


class ReservationResponse(ReservationBase):
    """Model for reservation responses including timestamps"""
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True  # Enable ORM mode for SQLAlchemy models