"""
Reservation API Routes
Includes create, lookup, update, and delete endpoints with name verification
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models.reservation import ReservationCreate, ReservationResponse, ReservationUpdate
from services.reservation_service import get_reservation_service

router = APIRouter(prefix="/api/reservations", tags=["reservations"])


class DeleteReservationRequest(BaseModel):
    """Request body for deleting a reservation"""
    name: str


class UpdateReservationRequest(BaseModel):
    """Request body for updating a reservation"""
    name: str  # For verification
    new_date: Optional[str] = None
    new_time: Optional[str] = None
    new_party_size: Optional[int] = None
    new_special_requests: Optional[str] = None


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


@router.delete("/{phone_number}")
async def delete_reservation(
    phone_number: str,
    request: DeleteReservationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a reservation after verifying ownership.
    
    Requires both phone number and name for security.
    """
    service = await get_reservation_service(db)
    deleted = await service.delete_reservation(phone_number, request.name)
    
    if not deleted:
        # Generic error message to not reveal if reservation exists
        raise HTTPException(
            status_code=404, 
            detail="No reservation found with those details"
        )
    
    return {"message": "Reservation cancelled successfully"}


@router.put("/{phone_number}", response_model=ReservationResponse)
async def update_reservation(
    phone_number: str,
    request: UpdateReservationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a reservation after verifying ownership.
    
    Requires both phone number and name for security.
    Only provided fields will be updated.
    """
    service = await get_reservation_service(db)
    
    # Build update data from request
    update_data = {}
    if request.new_date:
        update_data['reservation_date'] = request.new_date
    if request.new_time:
        update_data['reservation_time'] = request.new_time
    if request.new_party_size is not None:
        update_data['party_size'] = request.new_party_size
    if request.new_special_requests is not None:
        update_data['other_info'] = {'special_requests': request.new_special_requests}
    
    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields to update provided"
        )
    
    # Create ReservationUpdate object
    reservation_update = ReservationUpdate(**update_data)
    
    # Update with verification
    updated = await service.update_reservation(
        phone_number, 
        request.name,
        reservation_update
    )
    
    if not updated:
        # Generic error message to not reveal if reservation exists
        raise HTTPException(
            status_code=404,
            detail="No reservation found with those details"
        )
    
    return updated