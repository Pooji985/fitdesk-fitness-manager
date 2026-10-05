from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.base import init_db
from app.db.auth_store import init_auth_db, AuthSessionLocal, UserCredential
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import hash_password
from app.api.v1.api import api_router

def provision_demo_staff_accounts():
    """Provision demo Admin/Trainer credentials from environment variables."""
    demo_accounts = [
        ("alex.morgan@fitdesk.io", "DEMO_ADMIN_PASSWORD"),
        ("marcus.trainer@fitdesk.io", "DEMO_TRAINER_PASSWORD"),
    ]

    business_db = SessionLocal()
    auth_db = AuthSessionLocal()

    try:
        for email, password_env in demo_accounts:
            password = getattr(settings, password_env, None)

            if not password:
                continue

            user = (
                business_db.query(User)
                .filter(User.email == email)
                .first()
            )

            if not user or not user.is_active:
                continue

            credential = (
                auth_db.query(UserCredential)
                .filter(UserCredential.email == email)
                .first()
            )

            password_hash = hash_password(password)

            if credential:
                credential.user_id = user.id
                credential.password_hash = password_hash
            else:
                auth_db.add(
                    UserCredential(
                        email=email,
                        user_id=user.id,
                        password_hash=password_hash,
                    )
                )

        business_db.commit()
        auth_db.commit()

    finally:
        business_db.close()
        auth_db.close()
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure SQLite database tables and metadata are initialized
    init_db()
    init_auth_db()
    provision_demo_staff_accounts()
    yield
    # Shutdown logic (if needed in future)
    

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for FitDesk Fitness Class & Membership Manager with SQLite & FastAPI.",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Configure CORS for frontend access
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include v1 API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root():
    """Root endpoint welcoming users and directing to interactive documentation."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "docs_url": f"{settings.API_V1_STR}/docs",
        "redoc_url": f"{settings.API_V1_STR}/redoc",
        "health_check": f"{settings.API_V1_STR}/health",
    }
