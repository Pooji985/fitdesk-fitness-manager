from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.security import require_roles
from app.db.session import get_db
from app.models.booking import Booking
from app.models.fitness_class import FitnessClass
from app.models.user import User
from app.schemas.attendance import AttendanceRecord, AttendanceUpdate


router = APIRouter()


def _require_class_access(class_id: int, current_user: User, db: Session) -> FitnessClass:
    fitness_class = db.query(FitnessClass).filter(FitnessClass.id == class_id).first()
    if fitness_class is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found.")
    if current_user.role == "trainer" and fitness_class.trainer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Trainers may only access attendance for their assigned classes.")
    return fitness_class


def _attendance_record(booking: Booking) -> AttendanceRecord:
    return AttendanceRecord(
        booking_id=booking.id,
        member_id=booking.user_id,
        member_name=booking.user.name,
        class_id=booking.class_id,
        class_title=booking.fitness_class.title,
        start_time=booking.fitness_class.start_time,
        status=booking.status,
    )


@router.get("/classes/{class_id}", response_model=List[AttendanceRecord], summary="View class attendance roster")
def get_class_attendance(
    class_id: int,
    current_user: User = Depends(require_roles("admin", "trainer")),
    db: Session = Depends(get_db),
) -> List[AttendanceRecord]:
    _require_class_access(class_id, current_user, db)
    bookings = (
        db.query(Booking)
        .options(joinedload(Booking.user), joinedload(Booking.fitness_class))
        .filter(Booking.class_id == class_id, Booking.status != "cancelled")
        .join(User, Booking.user_id == User.id)
        .order_by(User.name.asc(), Booking.id.asc())
        .all()
    )
    return [_attendance_record(booking) for booking in bookings]


@router.patch("/bookings/{booking_id}", response_model=AttendanceRecord, summary="Mark or verify attendance for a booked member")
def update_booking_attendance(
    booking_id: int,
    attendance: AttendanceUpdate,
    current_user: User = Depends(require_roles("admin", "trainer")),
    db: Session = Depends(get_db),
) -> AttendanceRecord:
    booking = (
        db.query(Booking)
        .options(joinedload(Booking.user), joinedload(Booking.fitness_class))
        .filter(Booking.id == booking_id)
        .first()
    )
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")
    _require_class_access(booking.class_id, current_user, db)
    if booking.status == "cancelled":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cancelled bookings cannot be marked for attendance.")

    booking.status = attendance.status
    db.commit()
    db.refresh(booking)
    return _attendance_record(booking)