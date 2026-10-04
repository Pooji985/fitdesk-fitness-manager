from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.fitness_class import FitnessClass
from app.models.booking import Booking
from app.schemas.dashboard import DashboardMetricsResponse, StatItem, ActivityItem

router = APIRouter()


@router.get("/metrics", response_model=DashboardMetricsResponse, summary="Get role-tailored dashboard metrics and activity feed")
def get_dashboard_metrics(
    authenticated_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardMetricsResponse:
    """Fetch dashboard data for the identity verified from the bearer token."""
    target_user = authenticated_user

    user_role = target_user.role.lower()
    stats: List[StatItem] = []
    activities: List[ActivityItem] = []

    # 2. Role-specific metric computations
    if user_role == "admin":
        total_members = db.query(User).filter(User.role == "member").count()
        active_members = db.query(User).filter(User.role == "member", User.is_active == True).count()
        total_classes = db.query(FitnessClass).filter(FitnessClass.is_cancelled == False).count()
        outdoor_classes = db.query(FitnessClass).filter(FitnessClass.is_cancelled == False, FitnessClass.class_type == "outdoor").count()
        total_bookings = db.query(Booking).count()
        attended_bookings = db.query(Booking).filter(Booking.status == "attended").count()
        no_show_bookings = db.query(Booking).filter(Booking.status == "no_show").count()
        cancelled_bookings = db.query(Booking).filter(Booking.status == "cancelled").count()
        attendance_denominator = attended_bookings + no_show_bookings
        attendance_rate = (
            f"{round(attended_bookings / attendance_denominator * 100, 1)}%"
            if attendance_denominator
            else "N/A"
        )
        active_bookings = db.query(Booking).filter(Booking.status == "booked").count()
        
        total_capacity = db.query(func.sum(FitnessClass.capacity)).filter(FitnessClass.is_cancelled == False).scalar() or 0
        capacity_str = f"{round((active_bookings / total_capacity * 100), 1)}% booked" if total_capacity > 0 else "0% booked"

        stats = [
            StatItem(
                label="Active Members",
                value=str(active_members),
                change=f"{total_members} total registered",
                icon="Users",
                color="text-purple-400",
                bg="bg-purple-500/10",
            ),
            StatItem(
                label="Scheduled Classes",
                value=str(total_classes),
                change=f"{outdoor_classes} Outdoor sessions",
                icon="Calendar",
                color="text-emerald-400",
                bg="bg-emerald-500/10",
            ),
            StatItem(
                label="Total Bookings",
                value=str(total_bookings),
                change=capacity_str,
                icon="CheckCircle",
                color="text-cyan-400",
                bg="bg-cyan-500/10",
            ),
            StatItem(
                label="Weather Alerts",
                value="Monitoring",
                change=f"{outdoor_classes} outdoor venues ready",
                icon="CloudSun",
                color="text-amber-400",
                bg="bg-amber-500/10",
            ),
            StatItem(
                label="Attended",
                value=str(attended_bookings),
                change="Verified attendance",
                icon="CheckCircle",
                color="text-emerald-400",
                bg="bg-emerald-500/10",
            ),
            StatItem(
                label="No-Show",
                value=str(no_show_bookings),
                change="Missed booked sessions",
                icon="Users",
                color="text-rose-400",
                bg="bg-rose-500/10",
            ),
            StatItem(
                label="Cancelled Bookings",
                value=str(cancelled_bookings),
                change="Booking cancellations",
                icon="Calendar",
                color="text-slate-300",
                bg="bg-slate-500/10",
            ),
            StatItem(
                label="Attendance Rate",
                value=attendance_rate,
                change="Attended / (attended + no-show)",
                icon="TrendingUp",
                color="text-cyan-400",
                bg="bg-cyan-500/10",
            ),
        ]

        # Recent activities across the gym
        recent_bookings = (
            db.query(Booking)
            .options(joinedload(Booking.user), joinedload(Booking.fitness_class))
            .order_by(Booking.id.desc())
            .limit(5)
            .all()
        )
        for b in recent_bookings:
            badge_color = (
                "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
                if b.status == "attended"
                else "text-cyan-400 bg-cyan-500/10 border-cyan-500/20"
                if b.status == "booked"
                else "text-rose-400 bg-rose-500/10 border-rose-500/20"
            )
            class_name = b.fitness_class.title if b.fitness_class else "Unknown Class"
            member_name = b.user.name if b.user else "Unknown Member"
            time_str = b.booked_at.strftime("%b %d, %H:%M UTC") if b.booked_at else "Recently"
            activities.append(
                ActivityItem(
                    id=b.id,
                    title=class_name,
                    subtitle=f"Member: {member_name} • {b.fitness_class.location_name if b.fitness_class else 'Facility'}",
                    badge=b.status.capitalize(),
                    badge_color=badge_color,
                    time=time_str,
                )
            )

    elif user_role == "trainer":
        assigned_classes = (
            db.query(FitnessClass)
            .filter(FitnessClass.trainer_id == target_user.id, FitnessClass.is_cancelled == False)
            .count()
        )
        trainer_class_ids = [
            c[0] for c in db.query(FitnessClass.id).filter(FitnessClass.trainer_id == target_user.id).all()
        ]
        total_attendees = (
            db.query(Booking).filter(Booking.class_id.in_(trainer_class_ids)).count()
            if trainer_class_ids
            else 0
        )
        attended_count = (
            db.query(Booking)
            .filter(Booking.class_id.in_(trainer_class_ids), Booking.status == "attended")
            .count()
            if trainer_class_ids
            else 0
        )
        check_in_rate = (
            f"{round((attended_count / total_attendees * 100))}%"
            if total_attendees > 0
            else "100%"
        )
        outdoor_sessions = (
            db.query(FitnessClass)
            .filter(
                FitnessClass.trainer_id == target_user.id,
                FitnessClass.class_type == "outdoor",
                FitnessClass.is_cancelled == False,
            )
            .count()
        )

        stats = [
            StatItem(
                label="Assigned Classes",
                value=str(assigned_classes),
                change="Active coaching schedule",
                icon="Calendar",
                color="text-cyan-400",
                bg="bg-cyan-500/10",
            ),
            StatItem(
                label="Total Attendees",
                value=str(total_attendees),
                change=f"Across {assigned_classes} sessions",
                icon="Users",
                color="text-emerald-400",
                bg="bg-emerald-500/10",
            ),
            StatItem(
                label="Outdoor Sessions",
                value=str(outdoor_sessions),
                change="Open-Meteo checks ready",
                icon="CloudSun",
                color="text-amber-400",
                bg="bg-amber-500/10",
            ),
            StatItem(
                label="Check-In Rate",
                value=check_in_rate,
                change=f"{attended_count} verified check-ins",
                icon="Award",
                color="text-purple-400",
                bg="bg-purple-500/10",
            ),
        ]

        # Recent activities for this trainer
        if trainer_class_ids:
            recent_trainer_bookings = (
                db.query(Booking)
                .options(joinedload(Booking.user), joinedload(Booking.fitness_class))
                .filter(Booking.class_id.in_(trainer_class_ids))
                .order_by(Booking.id.desc())
                .limit(5)
                .all()
            )
            for b in recent_trainer_bookings:
                badge_color = (
                    "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
                    if b.status == "attended"
                    else "text-cyan-400 bg-cyan-500/10 border-cyan-500/20"
                    if b.status == "booked"
                    else "text-rose-400 bg-rose-500/10 border-rose-500/20"
                )
                class_name = b.fitness_class.title if b.fitness_class else "Assigned Class"
                member_name = b.user.name if b.user else "Member"
                time_str = b.booked_at.strftime("%b %d, %H:%M UTC") if b.booked_at else "Recently"
                activities.append(
                    ActivityItem(
                        id=b.id,
                        title=class_name,
                        subtitle=f"Attendee: {member_name} • {b.fitness_class.location_name if b.fitness_class else 'Studio'}",
                        badge=b.status.capitalize(),
                        badge_color=badge_color,
                        time=time_str,
                    )
                )

    else:  # member
        member_bookings = (
            db.query(Booking)
            .options(joinedload(Booking.fitness_class))
            .filter(Booking.user_id == target_user.id)
            .order_by(Booking.id.desc())
            .all()
        )
        active_bookings = sum(1 for b in member_bookings if b.status == "booked")
        attended_count = sum(1 for b in member_bookings if b.status == "attended")
        tier_label = target_user.membership_tier or "Unlimited All-Access"

        next_booking = next((b for b in member_bookings if b.status == "booked" and b.fitness_class), None)
        next_class_info = f"Next: {next_booking.fitness_class.title}" if next_booking else "No upcoming sessions"

        stats = [
            StatItem(
                label="My Active Bookings",
                value=str(active_bookings),
                change=next_class_info,
                icon="Calendar",
                color="text-emerald-400",
                bg="bg-emerald-500/10",
            ),
            StatItem(
                label="Membership Status",
                value="Active",
                change=tier_label,
                icon="Award",
                color="text-cyan-400",
                bg="bg-cyan-500/10",
            ),
            StatItem(
                label="Classes Attended",
                value=str(attended_count),
                change="Verified workouts completed",
                icon="TrendingUp",
                color="text-purple-400",
                bg="bg-purple-500/10",
            ),
            StatItem(
                label="Outdoor Weather",
                value="See Schedule",
                change="Check each outdoor class forecast",
                icon="CloudSun",
                color="text-amber-400",
                bg="bg-amber-500/10",
            ),
        ]

        for b in member_bookings[:5]:
            badge_color = (
                "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
                if b.status == "attended"
                else "text-cyan-400 bg-cyan-500/10 border-cyan-500/20"
                if b.status == "booked"
                else "text-rose-400 bg-rose-500/10 border-rose-500/20"
            )
            class_name = b.fitness_class.title if b.fitness_class else "Workout Session"
            loc = b.fitness_class.location_name if b.fitness_class else "Main Gym"
            activities.append(
                ActivityItem(
                    id=b.id,
                    title=class_name,
                    subtitle=f"{loc} • Type: {b.fitness_class.class_type.capitalize() if b.fitness_class else 'Indoor'}",
                    badge=b.status.capitalize(),
                    badge_color=badge_color,
                    time=b.booked_at.strftime("%b %d, %H:%M UTC") if b.booked_at else "Recently",
                )
            )

    return DashboardMetricsResponse(
        role=user_role,
        user_id=target_user.id,
        user_name=target_user.name,
        role_title=target_user.role_title or user_role.capitalize(),
        membership_tier=target_user.membership_tier,
        stats=stats,
        recent_activities=activities,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
