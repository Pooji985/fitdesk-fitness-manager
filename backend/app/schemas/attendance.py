from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class AttendanceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["attended", "no_show"]


class AttendanceRecord(BaseModel):
    booking_id: int
    member_id: int
    member_name: str
    class_id: int
    class_title: str
    start_time: datetime
    status: str
