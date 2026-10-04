from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class User(Base):
    """SQLAlchemy model representing a system user (Admin, Trainer, or Member)."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False, default="member")  # admin, trainer, member
    role_title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    membership_tier: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Unlimited All-Access, Basic, Drop-In
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    avatar: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    classes_trained: Mapped[List["FitnessClass"]] = relationship("FitnessClass", back_populates="trainer", cascade="all, delete-orphan")
    bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} name='{self.name}' role='{self.role}'>"
