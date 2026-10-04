from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class FitnessClass(Base):
    """SQLAlchemy model representing a scheduled fitness class (indoor or outdoor)."""
    __tablename__ = "fitness_classes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="General")  # Strength, HIIT, Yoga, Cardio, Running
    class_type: Mapped[str] = mapped_column(String(20), nullable=False, default="indoor")  # indoor, outdoor
    trainer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    location_name: Mapped[str] = mapped_column(String(150), nullable=False)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Reserved for Stage 4 Open-Meteo API
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Reserved for Stage 4 Open-Meteo API
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    trainer: Mapped["User"] = relationship("User", back_populates="classes_trained")
    bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="fitness_class", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<FitnessClass id={self.id} title='{self.title}' type='{self.class_type}' capacity={self.capacity}>"
