from datetime import datetime
from typing import Optional
from sqlalchemy import Index, String, Text, DateTime, ForeignKey, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Booking(Base):
    """SQLAlchemy model representing a member's class reservation and attendance record."""
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("fitness_classes.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="booked")  # booked, attended, cancelled, no_show
    booked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index(
            "uq_bookings_user_class_active",
            "user_id",
            "class_id",
            unique=True,
            sqlite_where=text("status != 'cancelled'"),
        ),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="bookings")
    fitness_class: Mapped["FitnessClass"] = relationship("FitnessClass", back_populates="bookings")

    def __repr__(self) -> str:
        return f"<Booking id={self.id} user_id={self.user_id} class_id={self.class_id} status='{self.status}'>"
