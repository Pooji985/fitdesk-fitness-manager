from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase
from app.db.session import engine, SessionLocal


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


def _add_member_profile_columns() -> None:
    if engine.dialect.name != "sqlite":
        return

    additions = {
        "phone": "VARCHAR(30)",
        "emergency_contact_name": "VARCHAR(100)",
        "emergency_contact_phone": "VARCHAR(30)",
    }
    with engine.begin() as connection:
        existing_columns = {column["name"] for column in inspect(connection).get_columns("users")}
        for column_name, column_type in additions.items():
            if column_name not in existing_columns:
                connection.exec_driver_sql(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")


def init_db() -> None:
    """Initialize database tables from Base metadata and run initial seeding if empty."""
    # Ensure all models are registered on Base.metadata
    import app.models  # noqa: F401
    from app.db.init_db import seed_database
    from app.models.booking import Booking

    Base.metadata.create_all(bind=engine)
    _add_member_profile_columns()
    next(index for index in Booking.__table__.indexes if index.name == "uq_bookings_user_class_active").create(
        bind=engine,
        checkfirst=True,
    )

    # Idempotently seed sample records if table is currently empty
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

