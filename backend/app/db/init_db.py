from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.fitness_class import FitnessClass
from app.models.booking import Booking


def seed_database(db: Session) -> None:
    """Safely and idempotently seed realistic initial data if the database is currently empty."""
    # Check if any users already exist
    existing_user = db.query(User).first()
    if existing_user:
        # Database already initialized with users, do not re-seed or duplicate records
        return

    now = datetime.now(timezone.utc)
    today_morning = now.replace(hour=9, minute=30, second=0, microsecond=0)
    tomorrow_morning = (now + timedelta(days=1)).replace(hour=7, minute=0, second=0, microsecond=0)
    tomorrow_noon = (now + timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)
    tomorrow_evening = (now + timedelta(days=1)).replace(hour=17, minute=30, second=0, microsecond=0)
    day_after_morning = (now + timedelta(days=2)).replace(hour=10, minute=0, second=0, microsecond=0)

    # 1. Create Core Personas (matching AuthContext.jsx) & sample members
    admin = User(
        id=1,
        name="Alex Morgan",
        email="alex.morgan@fitdesk.io",
        role="admin",
        role_title="Gym Administrator",
        avatar="AM",
        is_active=True,
    )
    trainer = User(
        id=2,
        name="Marcus Vance",
        email="marcus.trainer@fitdesk.io",
        role="trainer",
        role_title="Senior Coach (HIIT & Outdoor)",
        avatar="MV",
        is_active=True,
    )
    member_elena = User(
        id=3,
        name="Elena Rostova",
        email="elena.rostova@gmail.com",
        role="member",
        role_title="Premium Member",
        membership_tier="Unlimited All-Access",
        avatar="ER",
        is_active=True,
    )
    member_david = User(
        id=4,
        name="David Kim",
        email="david.kim@example.com",
        role="member",
        role_title="Basic Member",
        membership_tier="Basic Tier",
        avatar="DK",
        is_active=True,
    )
    member_maya = User(
        id=5,
        name="Maya Patel",
        email="maya.patel@example.com",
        role="member",
        role_title="Drop-In Member",
        membership_tier="Drop-In Pass",
        avatar="MP",
        is_active=True,
    )
    member_jordan = User(
        id=6,
        name="Jordan Lee",
        email="jordan.lee@example.com",
        role="member",
        role_title="Premium Member",
        membership_tier="Unlimited All-Access",
        avatar="JL",
        is_active=True,
    )

    db.add_all([admin, trainer, member_elena, member_david, member_maya, member_jordan])
    db.flush()

    # 2. Create Realistic Classes (Indoor & Outdoor with coordinates for Stage 4)
    c1 = FitnessClass(
        id=1,
        title="Outdoor Morning Bootcamp",
        description="High energy bodyweight drills, agility ladders, and interval cardio in the open park.",
        category="Bootcamp",
        class_type="outdoor",
        trainer_id=trainer.id,
        location_name="Central Park West Field",
        latitude=40.785091,
        longitude=-73.968285,
        capacity=20,
        start_time=tomorrow_morning,
        end_time=tomorrow_morning + timedelta(hours=1),
        is_cancelled=False,
    )
    c2 = FitnessClass(
        id=2,
        title="High Intensity Core & Cardio",
        description="Studio conditioning session combining rowing, kettlebells, and targeted core intervals.",
        category="HIIT",
        class_type="indoor",
        trainer_id=trainer.id,
        location_name="Studio A (Main Gym)",
        latitude=None,
        longitude=None,
        capacity=18,
        start_time=today_morning,
        end_time=today_morning + timedelta(hours=1),
        is_cancelled=False,
    )
    c3 = FitnessClass(
        id=3,
        title="Sunset Trail Run & Stretch",
        description="Scenic group run along riverbank trails followed by guided mobility and recovery stretching.",
        category="Running",
        class_type="outdoor",
        trainer_id=trainer.id,
        location_name="Riverside Trailhead",
        latitude=40.801000,
        longitude=-73.971000,
        capacity=15,
        start_time=tomorrow_evening,
        end_time=tomorrow_evening + timedelta(hours=1),
        is_cancelled=False,
    )
    c4 = FitnessClass(
        id=4,
        title="Power Vinyasa Flow",
        description="Dynamic mindful yoga flow building endurance, balance, and breath control.",
        category="Yoga",
        class_type="indoor",
        trainer_id=trainer.id,
        location_name="Studio B (Mind & Body)",
        latitude=None,
        longitude=None,
        capacity=16,
        start_time=day_after_morning,
        end_time=day_after_morning + timedelta(hours=1),
        is_cancelled=False,
    )
    c5 = FitnessClass(
        id=5,
        title="Strength & Conditioning Circuit",
        description="Full body barbell and dumbbell barbell stations focused on form and compound lifts.",
        category="Strength",
        class_type="indoor",
        trainer_id=trainer.id,
        location_name="Weight Room Annex",
        latitude=None,
        longitude=None,
        capacity=12,
        start_time=tomorrow_noon,
        end_time=tomorrow_noon + timedelta(hours=1),
        is_cancelled=False,
    )

    db.add_all([c1, c2, c3, c4, c5])
    db.flush()

    # 3. Create Realistic Bookings and Attendance Records
    bookings = [
        # Elena (Member 3)
        Booking(user_id=member_elena.id, class_id=c1.id, status="booked"),
        Booking(user_id=member_elena.id, class_id=c2.id, status="attended"),
        Booking(user_id=member_elena.id, class_id=c4.id, status="booked"),
        # David (Member 4)
        Booking(user_id=member_david.id, class_id=c2.id, status="attended"),
        Booking(user_id=member_david.id, class_id=c4.id, status="booked"),
        # Maya (Member 5)
        Booking(user_id=member_maya.id, class_id=c1.id, status="booked"),
        Booking(user_id=member_maya.id, class_id=c3.id, status="booked"),
        # Jordan (Member 6)
        Booking(user_id=member_jordan.id, class_id=c1.id, status="booked"),
        Booking(user_id=member_jordan.id, class_id=c2.id, status="attended"),
        Booking(user_id=member_jordan.id, class_id=c5.id, status="booked"),
    ]

    db.add_all(bookings)
    db.commit()
