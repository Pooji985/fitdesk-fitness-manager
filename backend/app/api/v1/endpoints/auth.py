import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.db.auth_store import UserCredential, get_auth_db
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import AuthenticatedUser, LoginRequest, RegisterRequest, TokenResponse


logger = logging.getLogger(__name__)
router = APIRouter()


def _check_auth_configuration() -> None:
    create_access_token(0)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    registration: RegisterRequest,
    db: Session = Depends(get_db),
    auth_db: Session = Depends(get_auth_db),
) -> TokenResponse:
    """Create a member account. Public registration cannot assign privileged roles."""
    _check_auth_configuration()
    email = registration.email
    existing_user = db.query(User).filter(func.lower(User.email) == email).first()
    if existing_user or auth_db.query(UserCredential).filter(UserCredential.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.")

    initials = "".join(part[0] for part in registration.name.split()[:2]).upper()
    user = User(
        name=registration.name,
        email=email,
        role="member",
        role_title="Member",
        membership_tier="Basic Tier",
        avatar=initials,
        is_active=True,
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.") from None

    auth_db.add(UserCredential(email=email, user_id=user.id, password_hash=hash_password(registration.password)))
    try:
        auth_db.commit()
    except Exception:
        auth_db.rollback()
        db.delete(user)
        db.commit()
        logger.exception("Could not persist credentials for newly registered user %s", user.id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Credential storage is unavailable. Please try again.",
        ) from None

    return TokenResponse(access_token=create_access_token(user.id), user=AuthenticatedUser.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
    auth_db: Session = Depends(get_auth_db),
) -> TokenResponse:
    _check_auth_configuration()
    user = db.query(User).filter(func.lower(User.email) == credentials.email).first()
    saved_credentials = auth_db.query(UserCredential).filter(UserCredential.email == credentials.email).first()
    if (
        user is None
        or saved_credentials is None
        or saved_credentials.user_id != user.id
        or not verify_password(credentials.password, saved_credentials.password_hash)
        or not user.is_active
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(access_token=create_access_token(user.id), user=AuthenticatedUser.model_validate(user))


@router.get("/me", response_model=AuthenticatedUser)
def get_authenticated_identity(current_user: User = Depends(get_current_user)) -> User:
    return current_user