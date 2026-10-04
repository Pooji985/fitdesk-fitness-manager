from fastapi import APIRouter
from app.api.v1.endpoints import auth, health, dashboard, classes, bookings, attendance, members

api_router = APIRouter()

# Include routers under /api/v1
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["Attendance"])
api_router.include_router(members.router, prefix="/members", tags=["Members"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(classes.router, prefix="/classes", tags=["Classes"])


