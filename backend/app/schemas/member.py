from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str
    avatar: Optional[str] = None
    membership_tier: Optional[str] = None
    phone: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    is_active: bool
    created_at: datetime


class MemberUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_active: Optional[bool] = None
    membership_tier: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=30)
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, max_length=30)

    @field_validator("membership_tier", "phone", "emergency_contact_name", "emergency_contact_phone")
    @classmethod
    def strip_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @model_validator(mode="after")
    def require_update_field(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one member field to update.")
        if "is_active" in self.model_fields_set and self.is_active is None:
            raise ValueError("is_active cannot be null.")
        return self


class MemberSelfProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    phone: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class MemberSelfProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: Optional[str] = Field(None, max_length=30)
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, max_length=30)

    @field_validator("phone", "emergency_contact_name", "emergency_contact_phone")
    @classmethod
    def strip_profile_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @model_validator(mode="after")
    def require_profile_field(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one profile field to update.")
        return self