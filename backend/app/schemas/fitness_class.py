from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class WeatherInfo(BaseModel):
    """Outdoor meteorological forecast details fetched from Open-Meteo."""
    status: str  # "optimal", "warning", "inclement", or "unavailable"
    temperature: Optional[float] = None
    precipitation_probability: Optional[int] = None
    wind_speed: Optional[float] = None
    condition: str
    alert_message: str
    badge_color: str


class TrainerBrief(BaseModel):
    """Brief representation of an assigned trainer."""
    id: int
    name: str
    role: Optional[str] = None
    role_title: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True


class FitnessClassBase(BaseModel):
    """Base attributes for a fitness class."""
    title: str = Field(..., min_length=3, max_length=120, description="Class title")
    description: Optional[str] = Field(None, max_length=1000, description="Class description")
    category: str = Field("General", max_length=50, description="Discipline/category (e.g., Strength, HIIT, Yoga)")
    class_type: str = Field("indoor", description="Class environment: 'indoor' or 'outdoor'")
    location_name: str = Field(..., min_length=2, max_length=150, description="Studio or venue name")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Venue latitude for Open-Meteo forecasts")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Venue longitude for Open-Meteo forecasts")
    capacity: int = Field(20, gt=0, le=200, description="Maximum attendee capacity")
    start_time: datetime = Field(..., description="Scheduled start time (ISO 8601)")
    end_time: datetime = Field(..., description="Scheduled end time (ISO 8601)")

    @field_validator("class_type")
    @classmethod
    def validate_class_type(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ["indoor", "outdoor"]:
            raise ValueError("class_type must be either 'indoor' or 'outdoor'")
        return clean

    @field_validator("title", "location_name", "category")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field cannot be blank")
        return stripped

    @model_validator(mode="after")
    def validate_time_window(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be strictly after start_time")
        return self


class FitnessClassCreate(FitnessClassBase):
    """Schema for scheduling a new fitness class."""
    trainer_id: int = Field(..., gt=0, description="ID of the trainer or coach conducting the session")


class FitnessClassUpdate(BaseModel):
    """Partial class update; server-side code validates the merged full class before saving."""
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = Field(None, min_length=3, max_length=120)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    class_type: Optional[str] = None
    trainer_id: Optional[int] = Field(None, gt=0)
    location_name: Optional[str] = Field(None, min_length=2, max_length=150)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    capacity: Optional[int] = Field(None, gt=0, le=200)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @field_validator("class_type")
    @classmethod
    def validate_optional_class_type(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        clean = value.strip().lower()
        if clean not in ["indoor", "outdoor"]:
            raise ValueError("class_type must be either 'indoor' or 'outdoor'")
        return clean

    @field_validator("title", "location_name", "category")
    @classmethod
    def strip_optional_required_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be blank")
        return stripped

    @model_validator(mode="after")
    def require_update_field(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one class field to update.")
        return self


class FitnessClassResponse(FitnessClassBase):
    """Detailed response schema for a scheduled fitness class."""
    id: int
    trainer_id: int
    trainer_name: Optional[str] = None
    trainer: Optional[TrainerBrief] = None
    capacity: int
    booked_count: int = 0
    remaining_spots: int = 0
    is_cancelled: bool = False
    created_at: datetime
    weather: Optional[WeatherInfo] = None

    class Config:
        from_attributes = True
