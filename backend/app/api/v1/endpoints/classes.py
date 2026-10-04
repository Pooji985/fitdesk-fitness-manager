from datetime import datetime, timezone
from typing import Optional, List
import logging
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy import func, text
from sqlalchemy.orm import Session, aliased, joinedload

from app.db.session import get_db
from app.core.security import require_roles
from app.models.user import User
from app.models.fitness_class import FitnessClass
from app.models.booking import Booking
from app.schemas.fitness_class import (
    FitnessClassCreate,
    FitnessClassUpdate,
    FitnessClassResponse,
    WeatherInfo,
    TrainerBrief,
)
from app.services.weather_service import get_outdoor_class_weather

logger = logging.getLogger(__name__)
router = APIRouter()

# Default coordinates for outdoor venues if coordinates not specified (Central Park West Field)
DEFAULT_OUTDOOR_LAT = 40.785091
DEFAULT_OUTDOOR_LON = -73.968285


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _build_class_response(cls: FitnessClass, include_weather: bool = True) -> FitnessClassResponse:
    """Helper to convert a FitnessClass ORM model to FitnessClassResponse with weather enrichment."""
    # Count active bookings
    booked_count = sum(1 for b in cls.bookings if b.status != "cancelled")
    remaining = max(0, cls.capacity - booked_count)

    weather_info: Optional[WeatherInfo] = None
    if cls.class_type.lower() == "outdoor" and include_weather:
        lat = cls.latitude if cls.latitude is not None else DEFAULT_OUTDOOR_LAT
        lon = cls.longitude if cls.longitude is not None else DEFAULT_OUTDOOR_LON
        raw_weather = get_outdoor_class_weather(lat, lon, cls.start_time)
        weather_info = WeatherInfo(
            status=raw_weather["status"],
            temperature=raw_weather["temperature"],
            precipitation_probability=raw_weather["precipitation_probability"],
            wind_speed=raw_weather["wind_speed"],
            condition=raw_weather["condition"],
            alert_message=raw_weather["alert_message"],
            badge_color=raw_weather["badge_color"],
        )

    trainer_brief = None
    trainer_name = "Assigned Coach"
    if cls.trainer:
        trainer_name = cls.trainer.name
        trainer_brief = TrainerBrief(
            id=cls.trainer.id,
            name=cls.trainer.name,
            role_title=cls.trainer.role_title,
            email=cls.trainer.email,
        )

    return FitnessClassResponse(
        id=cls.id,
        title=cls.title,
        description=cls.description,
        category=cls.category,
        class_type=cls.class_type.lower(),
        trainer_id=cls.trainer_id,
        trainer_name=trainer_name,
        trainer=trainer_brief,
        location_name=cls.location_name,
        latitude=cls.latitude,
        longitude=cls.longitude,
        capacity=cls.capacity,
        start_time=cls.start_time,
        end_time=cls.end_time,
        booked_count=booked_count,
        remaining_spots=remaining,
        is_cancelled=cls.is_cancelled,
        created_at=cls.created_at or datetime.now(timezone.utc),
        weather=weather_info,
    )


@router.get("/trainers", response_model=List[TrainerBrief], summary="List available trainers and coaches for class assignment")
def get_available_trainers(db: Session = Depends(get_db)) -> List[TrainerBrief]:
    """Returns all active trainers and staff eligible to lead fitness classes."""
    trainers = (
        db.query(User)
        .filter(User.role.in_(["trainer", "admin"]), User.is_active == True)
        .order_by(User.name.asc())
        .all()
    )
    return [
        TrainerBrief(
            id=t.id,
            name=t.name,
            role=t.role,
            role_title=t.role_title or ("Lead Coach" if t.role == "trainer" else "Gym Administrator"),
            email=t.email,
        )
        for t in trainers
    ]


@router.get("", response_model=List[FitnessClassResponse], summary="List fitness classes with optional filters and weather indicators")
def list_fitness_classes(
    class_type: Optional[str] = Query(None, description="Filter by class environment ('indoor' or 'outdoor')"),
    category: Optional[str] = Query(None, description="Filter by discipline/category (e.g., Strength, HIIT, Yoga, Running)"),
    trainer_id: Optional[int] = Query(None, description="Filter by instructor ID"),
    search: Optional[str] = Query(None, description="Search keyword in title, category, or location"),
    upcoming_only: bool = Query(False, description="Return classes whose start time has not passed"),
    include_weather: bool = Query(True, description="Query Open-Meteo for outdoor classes"),
    db: Session = Depends(get_db),
) -> List[FitnessClassResponse]:
    """Retrieve scheduled fitness classes enriched with live booking metrics and Open-Meteo weather forecasts."""
    query = (
        db.query(FitnessClass)
        .options(joinedload(FitnessClass.trainer), joinedload(FitnessClass.bookings))
        .filter(FitnessClass.is_cancelled == False)
    )

    if class_type:
        clean_type = class_type.strip().lower()
        if clean_type in ["indoor", "outdoor"]:
            query = query.filter(FitnessClass.class_type == clean_type)

    if category and category.lower() != "all":
        query = query.filter(FitnessClass.category.ilike(f"%{category.strip()}%"))

    if trainer_id:
        query = query.filter(FitnessClass.trainer_id == trainer_id)

    if upcoming_only:
        query = query.filter(FitnessClass.start_time >= datetime.now(timezone.utc).replace(tzinfo=None))

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            FitnessClass.title.ilike(search_pattern)
            | FitnessClass.location_name.ilike(search_pattern)
            | FitnessClass.category.ilike(search_pattern)
        )

    classes = query.order_by(FitnessClass.start_time.asc()).all()

    return [_build_class_response(cls, include_weather=include_weather) for cls in classes]


@router.get("/{class_id}", response_model=FitnessClassResponse, summary="Get details and weather forecast for a specific class")
def get_fitness_class(
    class_id: int,
    include_weather: bool = Query(True, description="Query Open-Meteo for outdoor class weather"),
    db: Session = Depends(get_db),
) -> FitnessClassResponse:
    """Retrieve a single fitness class with assigned trainer, active capacity, and weather details."""
    cls = (
        db.query(FitnessClass)
        .options(joinedload(FitnessClass.trainer), joinedload(FitnessClass.bookings))
        .filter(FitnessClass.id == class_id)
        .first()
    )
    if not cls:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fitness class with ID {class_id} not found.",
        )

    return _build_class_response(cls, include_weather=include_weather)


@router.post("", response_model=FitnessClassResponse, status_code=status.HTTP_201_CREATED, summary="Schedule a new fitness class (Admin only)")
def create_fitness_class(
    class_in: FitnessClassCreate,
    _current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> FitnessClassResponse:
    """Creates and schedules a class for an authenticated Admin."""
    # Verify the assigned instructor is an active trainer or administrator.
    trainer = db.query(User).filter(User.id == class_in.trainer_id, User.is_active == True).first()
    if not trainer or trainer.role not in {"trainer", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Active trainer with ID {class_in.trainer_id} does not exist in the database.",
        )

    # 3. Setup coordinates for outdoor classes
    lat = class_in.latitude
    lon = class_in.longitude
    if class_in.class_type.lower() == "outdoor":
        if lat is None or lon is None:
            lat = DEFAULT_OUTDOOR_LAT
            lon = DEFAULT_OUTDOOR_LON

    # 4. Instantiate and commit the new class
    new_class = FitnessClass(
        title=class_in.title,
        description=class_in.description,
        category=class_in.category,
        class_type=class_in.class_type.lower(),
        trainer_id=class_in.trainer_id,
        location_name=class_in.location_name,
        latitude=lat,
        longitude=lon,
        capacity=class_in.capacity,
        start_time=class_in.start_time,
        end_time=class_in.end_time,
        is_cancelled=False,
    )

    db.add(new_class)
    db.commit()
    db.refresh(new_class)

    # Reload relationships
    cls = (
        db.query(FitnessClass)
        .options(joinedload(FitnessClass.trainer), joinedload(FitnessClass.bookings))
        .filter(FitnessClass.id == new_class.id)
        .first()
    )

    return _build_class_response(cls, include_weather=True)


@router.patch("/{class_id}", response_model=FitnessClassResponse, summary="Edit a fitness class (Admin only)")
def update_fitness_class(
    class_id: int,
    class_update: FitnessClassUpdate,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> FitnessClassResponse:
    """Apply a partial Admin edit while preserving bookings and attendance records."""
    db.execute(text("BEGIN IMMEDIATE"))
    fitness_class = (
        db.query(FitnessClass)
        .options(joinedload(FitnessClass.trainer), joinedload(FitnessClass.bookings))
        .filter(FitnessClass.id == class_id)
        .first()
    )
    if fitness_class is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found.")
    if fitness_class.is_cancelled:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cancelled classes cannot be edited.")

    merged_values = {
        "title": fitness_class.title,
        "description": fitness_class.description,
        "category": fitness_class.category,
        "class_type": fitness_class.class_type,
        "trainer_id": fitness_class.trainer_id,
        "location_name": fitness_class.location_name,
        "latitude": fitness_class.latitude,
        "longitude": fitness_class.longitude,
        "capacity": fitness_class.capacity,
        "start_time": fitness_class.start_time,
        "end_time": fitness_class.end_time,
    }
    merged_values.update(class_update.model_dump(exclude_unset=True))
    try:
        validated = FitnessClassCreate.model_validate(merged_values)
    except ValidationError as error:
        raise RequestValidationError(error.errors()) from error

    if "trainer_id" in class_update.model_fields_set:
        trainer = (
            db.query(User)
            .filter(User.id == validated.trainer_id, User.is_active.is_(True), User.role.in_(["trainer", "admin"]))
            .first()
        )
        if trainer is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An active trainer must be assigned to the class.")

    active_booking_count = (
        db.query(func.count(Booking.id))
        .filter(Booking.class_id == class_id, Booking.status != "cancelled")
        .scalar()
        or 0
    )
    if validated.capacity < active_booking_count:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Capacity cannot be lower than the {active_booking_count} existing bookings.",
        )

    class_bookings = (
        db.query(Booking.user_id)
        .filter(Booking.class_id == class_id, Booking.status == "booked")
        .distinct()
        .all()
    )
    other_class = aliased(FitnessClass)
    for (member_id,) in class_bookings:
        conflicting_booking = (
            db.query(Booking.id)
            .join(other_class, Booking.class_id == other_class.id)
            .filter(
                Booking.user_id == member_id,
                Booking.class_id != class_id,
                Booking.status == "booked",
                other_class.is_cancelled.is_(False),
                other_class.start_time < validated.end_time,
                other_class.end_time > validated.start_time,
            )
            .first()
        )
        if conflicting_booking:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The updated time would overlap an enrolled member's other booking.",
            )

    if class_bookings and _as_utc(validated.start_time) <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A class with existing bookings cannot be moved to a time that has already started.",
        )

    latitude = validated.latitude
    longitude = validated.longitude
    if validated.class_type == "outdoor" and (latitude is None or longitude is None):
        latitude = DEFAULT_OUTDOOR_LAT
        longitude = DEFAULT_OUTDOOR_LON

    fitness_class.title = validated.title
    fitness_class.description = validated.description
    fitness_class.category = validated.category
    fitness_class.class_type = validated.class_type
    fitness_class.trainer_id = validated.trainer_id
    fitness_class.location_name = validated.location_name
    fitness_class.latitude = latitude
    fitness_class.longitude = longitude
    fitness_class.capacity = validated.capacity
    fitness_class.start_time = validated.start_time
    fitness_class.end_time = validated.end_time
    db.commit()

    updated_class = (
        db.query(FitnessClass)
        .options(joinedload(FitnessClass.trainer), joinedload(FitnessClass.bookings))
        .filter(FitnessClass.id == class_id)
        .one()
    )
    return _build_class_response(updated_class, include_weather=False)


@router.post("/{class_id}/cancel", response_model=FitnessClassResponse, summary="Cancel a fitness class (Admin only)")
def cancel_fitness_class(
    class_id: int,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> FitnessClassResponse:
    """Soft-cancel a class, preserving all bookings and attendance history."""
    db.execute(text("BEGIN IMMEDIATE"))
    fitness_class = (
        db.query(FitnessClass)
        .options(joinedload(FitnessClass.trainer), joinedload(FitnessClass.bookings))
        .filter(FitnessClass.id == class_id)
        .first()
    )
    if fitness_class is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found.")

    if not fitness_class.is_cancelled:
        fitness_class.is_cancelled = True
        db.commit()
        fitness_class = (
            db.query(FitnessClass)
            .options(joinedload(FitnessClass.trainer), joinedload(FitnessClass.bookings))
            .filter(FitnessClass.id == class_id)
            .one()
        )

    return _build_class_response(fitness_class, include_weather=False)
