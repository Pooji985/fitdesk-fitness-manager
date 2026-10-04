from typing import List, Optional
from pydantic import BaseModel, Field


class StatItem(BaseModel):
    """Single metric KPI card item."""
    label: str
    value: str
    change: str
    icon: str  # Users, Calendar, CheckCircle, CloudSun, Award, TrendingUp
    color: str
    bg: str


class ActivityItem(BaseModel):
    """Recent class booking or attendance activity log."""
    id: int
    title: str
    subtitle: str
    badge: str
    badge_color: str
    time: str


class DashboardMetricsResponse(BaseModel):
    """Full role-tailored dashboard metrics and activity response."""
    role: str
    user_id: int
    user_name: str
    role_title: str
    membership_tier: Optional[str] = None
    stats: List[StatItem]
    recent_activities: List[ActivityItem] = Field(default_factory=list)
    generated_at: str
