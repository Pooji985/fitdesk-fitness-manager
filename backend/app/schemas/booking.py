from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BookingCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    class_id: int = Field(..., gt=0)


class BookingClassInfo(BaseModel):
    id: int
    title: str
    category: str
    class_type: str
    location_name: str
    trainer_name: str
    start_time: datetime
    end_time: datetime
    is_cancelled: bool = False


class BookingResponse(BaseModel):
    id: int
    user_id: int
    class_id: int
    status: str
    booked_at: datetime
    fitness_class: BookingClassInfo