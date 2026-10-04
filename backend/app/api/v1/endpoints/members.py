from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.member import (
    MemberResponse,
    MemberSelfProfileResponse,
    MemberSelfProfileUpdate,
    MemberUpdate,
)


router = APIRouter()


@router.get("/me", response_model=MemberSelfProfileResponse, summary="Get the authenticated member's own profile")
def get_my_member_profile(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "member":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Member profile access is limited to members.")
    return current_user


@router.patch("/me", response_model=MemberSelfProfileResponse, summary="Update the authenticated member's contact profile")
def update_my_member_profile(
    profile_update: MemberSelfProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    if current_user.role != "member":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Member profile updates are limited to members.")

    for field_name in profile_update.model_fields_set:
        setattr(current_user, field_name, getattr(profile_update, field_name))
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("", response_model=List[MemberResponse], summary="List gym members (Admin only)")
def list_members(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
) -> List[MemberResponse]:
    return db.query(User).filter(User.role == "member").order_by(User.name.asc()).all()


@router.patch("/{member_id}", response_model=MemberResponse, summary="Update a member profile, status, or tier (Admin only)")
def update_member(
    member_id: int,
    member_update: MemberUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
) -> User:
    member = db.query(User).filter(User.id == member_id, User.role == "member").first()
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")

    changed_fields = member_update.model_fields_set
    for field_name in changed_fields:
        setattr(member, field_name, getattr(member_update, field_name))
    db.commit()
    db.refresh(member)
    return member