from typing import Generator

from sqlalchemy import DateTime, Integer, String, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.core.config import settings


connect_args = {"check_same_thread": False} if settings.AUTH_DATABASE_URL.startswith("sqlite") else {}
auth_engine = create_engine(settings.AUTH_DATABASE_URL, connect_args=connect_args, echo=False)
AuthSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=auth_engine)


class AuthBase(DeclarativeBase):
    pass


class UserCredential(AuthBase):
    __tablename__ = "user_credentials"

    email: Mapped[str] = mapped_column(String(120), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def init_auth_db() -> None:
    """Create the separate credential store without changing either existing FitDesk database."""
    AuthBase.metadata.create_all(bind=auth_engine)


def get_auth_db() -> Generator[Session, None, None]:
    db = AuthSessionLocal()
    try:
        yield db
    finally:
        db.close()