"""
Reservation API Routes (Simplified for Demo)
Only includes create and lookup endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.reservation import ReservationCreate, ReservationResponse
from services.reservation_service import get_reservation_service

router = APIRouter(prefix="/api/reservations", tags=["reservations"])


@router.post("", response_model=ReservationResponse)
async def create_reservation(
    reservation: ReservationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new reservation
    
    This endpoint is called by the RealtimeAgent tools when making a reservation.
    """
    try:
        service = await get_reservation_service(db)
        result = await service.create_reservation(reservation)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create reservation: {str(e)}")


@router.get("/{phone_number}", response_model=ReservationResponse)
async def get_reservation(
    phone_number: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get reservation by phone number
    
    Allows customers to look up their existing reservation.
    """
    service = await get_reservation_service(db)
    reservation = await service.get_reservation_by_phone(phone_number)
    
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    return reservation