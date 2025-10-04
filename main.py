from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from src.api.contacts import router as contacts_router
from src.api.auth import router as auth_router
from src.api.cache import router as cache_router
from src.api.admin import router as admin_router
from src.database.db import engine
from src.database.models import Base
from src.services.rate_limiter import limiter, custom_rate_limit_handler
from src.services.middleware import setup_role_middleware
from src.conf.config import settings

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app instance
app = FastAPI(
    title="Contacts API with JWT Auth & Rate Limiting & CORS",
    description="A contacts management API with JWT authentication, rate limiting, CORS support and PostgreSQL database",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

# Setup role-based middleware
setup_role_middleware(app)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(contacts_router, prefix="/api", tags=["contacts"])
app.include_router(cache_router, prefix="/api", tags=["cache"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to Contacts API"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "database": "connected"}


@app.get("/cors-test")
async def cors_test():
    """CORS test endpoint"""
    return {
        "message": "CORS is working!",
        "allowed_origins": settings.cors_origins,
        "credentials_allowed": settings.cors_allow_credentials,
        "allowed_methods": settings.cors_allow_methods,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
