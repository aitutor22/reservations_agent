"""
Reservation Service
Business logic for reservation management with PostgreSQL
"""

from typing import List, Optional, Dict, Any
from datetime import date, time, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, delete, update
from sqlalchemy.exc import IntegrityError
import logging

from models.db_models import Reservation
from models.reservation import ReservationCreate, ReservationUpdate, ReservationResponse
from utils.name_matching import split_and_match_names

logger = logging.getLogger(__name__)


class ReservationService:
    """Service class for managing reservations"""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize reservation service
        
        Args:
            db: AsyncSession for database operations
        """
        self.db = db
    
    async def create_reservation(self, reservation_data: ReservationCreate) -> ReservationResponse:
        """
        Create a new reservation
        
        Args:
            reservation_data: Reservation creation data
            
        Returns:
            Created reservation
            
        Raises:
            ValueError: If phone number already has a reservation
        """
        try:
            # Check if phone number already has a reservation
            existing = await self.get_reservation_by_phone(reservation_data.phone_number)
            if existing:
                raise ValueError(f"Phone number {reservation_data.phone_number} already has a reservation")
            
            # Create new reservation
            db_reservation = Reservation(
                phone_number=reservation_data.phone_number,
                name=reservation_data.name,
                reservation_date=date.fromisoformat(reservation_data.reservation_date),
                reservation_time=time.fromisoformat(reservation_data.reservation_time),
                party_size=reservation_data.party_size,
                other_info=reservation_data.other_info or {}
            )
            
            self.db.add(db_reservation)
            await self.db.commit()
            await self.db.refresh(db_reservation)
            
            logger.info(f"Created reservation for {db_reservation.phone_number}")
            return ReservationResponse.from_orm(db_reservation)
            
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Database integrity error: {e}")
            raise ValueError("Reservation already exists for this phone number")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating reservation: {e}")
            raise
    
    async def verify_reservation_owner(
        self, 
        phone_number: str, 
        name: str
    ) -> Optional[ReservationResponse]:
        """
        Verify reservation ownership by checking both phone and name.
        
        Args:
            phone_number: Customer phone number
            name: Customer name (will use fuzzy matching)
            
        Returns:
            Reservation if both phone and name match, None otherwise
        """
        try:
            # First get the reservation by phone
            stmt = select(Reservation).where(Reservation.phone_number == phone_number)
            result = await self.db.execute(stmt)
            reservation = result.scalar_one_or_none()
            
            if not reservation:
                return None
            
            # Verify the name matches (with fuzzy matching)
            if not split_and_match_names(name, reservation.name):
                logger.warning(f"Name verification failed for {phone_number}: provided '{name}' vs stored '{reservation.name}'")
                return None
            
            logger.info(f"Verified reservation ownership for {phone_number}")
            return ReservationResponse.from_orm(reservation)
            
        except Exception as e:
            logger.error(f"Error verifying reservation: {e}")
            raise
    
    async def get_reservation_by_phone(self, phone_number: str) -> Optional[ReservationResponse]:
        """
        Get reservation by phone number
        
        Args:
            phone_number: Customer phone number
            
        Returns:
            Reservation if found, None otherwise
        """
        try:
            stmt = select(Reservation).where(Reservation.phone_number == phone_number)
            result = await self.db.execute(stmt)
            reservation = result.scalar_one_or_none()
            
            if reservation:
                return ReservationResponse.from_orm(reservation)
            return None
            
        except Exception as e:
            logger.error(f"Error fetching reservation: {e}")
            raise
    
    async def update_reservation(
        self,
        phone_number: str,
        name: str,
        update_data: ReservationUpdate
    ) -> Optional[ReservationResponse]:
        """
        Update an existing reservation after verifying ownership
        
        Args:
            phone_number: Customer phone number
            name: Customer name for verification
            update_data: Fields to update
            
        Returns:
            Updated reservation if verified and found, None otherwise
        """
        try:
            # Check if reservation exists and verify ownership
            stmt = select(Reservation).where(Reservation.phone_number == phone_number)
            result = await self.db.execute(stmt)
            reservation = result.scalar_one_or_none()
            
            if not reservation:
                return None
                
            # Verify name matches
            if not split_and_match_names(name, reservation.name):
                logger.warning(f"Update denied - name verification failed for {phone_number}")
                return None
            
            # Update fields
            update_dict = update_data.dict(exclude_unset=True)
            
            # Convert date and time strings to proper types
            if 'reservation_date' in update_dict:
                update_dict['reservation_date'] = date.fromisoformat(update_dict['reservation_date'])
            if 'reservation_time' in update_dict:
                update_dict['reservation_time'] = time.fromisoformat(update_dict['reservation_time'])
            
            # Update the reservation
            for key, value in update_dict.items():
                setattr(reservation, key, value)
            
            reservation.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(reservation)
            
            logger.info(f"Updated reservation for {phone_number}")
            return ReservationResponse.from_orm(reservation)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating reservation: {e}")
            raise
    
    async def delete_reservation(self, phone_number: str, name: str) -> bool:
        """
        Cancel/delete a reservation after verifying ownership
        
        Args:
            phone_number: Customer phone number
            name: Customer name for verification
            
        Returns:
            True if deleted, False if not found or verification failed
        """
        try:
            # First verify ownership
            verified = await self.verify_reservation_owner(phone_number, name)
            if not verified:
                logger.warning(f"Delete denied - verification failed for {phone_number}")
                return False
            
            # Now delete the reservation
            stmt = delete(Reservation).where(Reservation.phone_number == phone_number)
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            deleted = result.rowcount > 0
            if deleted:
                logger.info(f"Deleted reservation for {phone_number}")
            else:
                logger.warning(f"No reservation found for {phone_number}")
            
            return deleted
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting reservation: {e}")
            raise
    
    async def list_all_reservations(
        self,
        skip: int = 0,
        limit: int = 100,
        filter_date: Optional[str] = None
    ) -> List[ReservationResponse]:
        """
        List all reservations with optional filtering
        
        Args:
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            filter_date: Optional date filter (ISO format)
            
        Returns:
            List of reservations
        """
        try:
            stmt = select(Reservation)
            
            # Apply date filter if provided
            if filter_date:
                filter_date_obj = date.fromisoformat(filter_date)
                stmt = stmt.where(Reservation.reservation_date == filter_date_obj)
            
            # Order by date and time
            stmt = stmt.order_by(
                Reservation.reservation_date,
                Reservation.reservation_time
            ).offset(skip).limit(limit)
            
            result = await self.db.execute(stmt)
            reservations = result.scalars().all()
            
            return [ReservationResponse.from_orm(r) for r in reservations]
            
        except Exception as e:
            logger.error(f"Error listing reservations: {e}")
            raise
    
    async def check_availability(
        self,
        check_date: str,
        check_time: str,
        party_size: int
    ) -> Dict[str, Any]:
        """
        Check availability for a given date/time
        (Simplified version - always returns available since we don't model tables)
        
        Args:
            check_date: Date to check (ISO format)
            check_time: Time to check (HH:MM format)
            party_size: Number of people
            
        Returns:
            Availability status
        """
        try:
            # For MVP, always return available
            # In production, this would check against table capacity
            return {
                "available": True,
                "date": check_date,
                "time": check_time,
                "party_size": party_size,
                "message": "Tables available for your party"
            }
            
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            raise


async def get_reservation_service(db: AsyncSession) -> ReservationService:
    """
    Factory function to create reservation service
    
    Args:
        db: Database session
        
    Returns:
        ReservationService instance
    """
    return ReservationService(db)