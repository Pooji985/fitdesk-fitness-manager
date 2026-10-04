from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.security import get_current_user, require_roles
from app.db.session import get_db
from app.models.booking import Booking
from app.models.fitness_class import FitnessClass
from app.models.user import User
from app.schemas.booking import BookingClassInfo, BookingCreate, BookingResponse


router = APIRouter()


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _booking_response(booking: Booking) -> BookingResponse:
    fitness_class = booking.fitness_class
    return BookingResponse(
        id=booking.id,
        user_id=booking.user_id,
        class_id=booking.class_id,
        status=booking.status,
        booked_at=booking.booked_at,
        fitness_class=BookingClassInfo(
            id=fitness_class.id,
            title=fitness_class.title,
            category=fitness_class.category,
            class_type=fitness_class.class_type,
            location_name=fitness_class.location_name,
            trainer_name=fitness_class.trainer.name if fitness_class.trainer else "Assigned Coach",
            start_time=fitness_class.start_time,
            end_time=fitness_class.end_time,
            is_cancelled=fitness_class.is_cancelled,
        ),
    )


@router.get("", response_model=List[BookingResponse], summary="List bookings for the authenticated user")
def list_my_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[BookingResponse]:
    bookings = (
        db.query(Booking)
        .options(joinedload(Booking.fitness_class).joinedload(FitnessClass.trainer))
        .filter(Booking.user_id == current_user.id)
        .join(FitnessClass, Booking.class_id == FitnessClass.id)
        .order_by(FitnessClass.start_time.desc(), Booking.id.desc())
        .all()
    )
    return [_booking_response(booking) for booking in bookings]


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED, summary="Book an available class as a member")
def create_booking(
    booking_in: BookingCreate,
    current_user: User = Depends(require_roles("member")),
    db: Session = Depends(get_db),
) -> BookingResponse:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="An active membership is required to book a class.")

    # Serialize SQLite booking writes so capacity and overlap checks remain valid under concurrent requests.
    db.execute(text("BEGIN IMMEDIATE"))

    fitness_class = (
        db.query(FitnessClass)
        .filter(FitnessClass.id == booking_in.class_id)
        .with_for_update()
        .first()
    )
    if fitness_class is None or fitness_class.is_cancelled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Available class not found.")
    if _as_utc(fitness_class.start_time) <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bookings are closed after a class has started.")

    existing = (
        db.query(Booking)
        .filter(
            Booking.user_id == current_user.id,
            Booking.class_id == fitness_class.id,
            Booking.status != "cancelled",
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already have a booking for this class.")

    overlapping = (
        db.query(Booking.id)
        .join(FitnessClass, Booking.class_id == FitnessClass.id)
        .filter(
            Booking.user_id == current_user.id,
            Booking.status == "booked",
            FitnessClass.is_cancelled.is_(False),
            FitnessClass.start_time < fitness_class.end_time,
            FitnessClass.end_time > fitness_class.start_time,
        )
        .first()
    )
    if overlapping:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already have a booking that overlaps this class.")

    booked_count = (
        db.query(func.count(Booking.id))
        .filter(Booking.class_id == fitness_class.id, Booking.status != "cancelled")
        .scalar()
        or 0
    )
    if booked_count >= fitness_class.capacity:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This class has reached its capacity.")

    booking = Booking(user_id=current_user.id, class_id=fitness_class.id, status="booked")
    db.add(booking)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already have a booking for this class.") from None

    saved_booking = (
        db.query(Booking)
        .options(joinedload(Booking.fitness_class).joinedload(FitnessClass.trainer))
        .filter(Booking.id == booking.id)
        .one()
    )
    return _booking_response(saved_booking)


@router.post("/{booking_id}/cancel", response_model=BookingResponse, summary="Cancel the authenticated member's booking")
def cancel_booking(
    booking_id: int,
    current_user: User = Depends(require_roles("member")),
    db: Session = Depends(get_db),
) -> BookingResponse:
    db.execute(text("BEGIN IMMEDIATE"))
    booking = (
        db.query(Booking)
        .options(joinedload(Booking.fitness_class).joinedload(FitnessClass.trainer))
        .filter(Booking.id == booking_id)
        .first()
    )
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You may only cancel your own bookings.")
    if booking.status != "booked":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only active bookings can be cancelled.")

    booking.status = "cancelled"
    db.commit()
    db.refresh(booking)
    return _booking_response(booking)