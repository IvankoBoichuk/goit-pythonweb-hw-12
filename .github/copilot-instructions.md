# Copilot Instructions for FastAPI Contacts API

This is a **multi-layered FastAPI application** with JWT authentication, PostgreSQL database, and Redis rate limiting. Understanding the architectural patterns and conventions is crucial for maintaining consistency.

## Architecture Overview

### Layer Structure (Repository Pattern)
- **`src/api/`** - FastAPI routers with authentication decorators and rate limiting
- **`src/services/`** - Business logic layer (auth, cloudinary, email, contacts)
- **`src/repository/`** - Data access layer with async/await patterns
- **`src/database/`** - SQLAlchemy models and session management
- **`src/schemas.py`** - Pydantic models for request/response validation

### Key Design Patterns

**Repository Pattern**: All database operations go through repository classes
```python
# Example from src/repository/contacts.py
class ContactRepository:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_contacts(self, skip: int = 0, limit: int = 100) -> List[Contact]:
        return self.db.query(Contact).offset(skip).limit(limit).all()
```

**Service Layer for Business Logic**: Complex operations use service classes
```python
# Example from src/services/auth.py
class AuthService:
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        # JWT creation logic
```

**User Context Isolation**: All contacts are filtered by `user_id` - never expose cross-user data
```python
# Always filter by user in contact operations
contacts = db.query(Contact).filter(Contact.user_id == current_user.id).all()
```

## Critical Development Patterns

### Authentication Flow
- Uses `HTTPBearer` token authentication with JWT
- Password hashing with `pbkdf2_sha256` (not bcrypt)
- Email verification workflow with tokens stored in `User.verification_token`
- Rate limiting applied per-endpoint using `@limiter.limit("5/minute")` decorators

### Rate Limiting Convention
Apply to all auth endpoints and sensitive operations:
```python
@router.post("/register")
@limiter.limit("5/minute")  # Always include rate limits on auth endpoints
async def register_user(request: Request, ...):
```

### Database Session Pattern
Always use dependency injection for database sessions:
```python
async def endpoint(db: Session = Depends(get_db)):
    # Use repository pattern, not direct ORM calls
    repo = ContactRepository(db)
```

### Error Handling Standard
Use FastAPI's `HTTPException` with specific status codes:
```python
raise HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Username already registered"
)
```

## Configuration Management

**Settings Pattern**: All configuration via `src/conf/config.py` using Pydantic `BaseModel`
- Environment variables loaded with `python-dotenv`
- Defaults provided for development (see `Settings` class)
- CORS, rate limiting, and external services configured centrally

**Docker Environment**: Different DATABASE_URL and REDIS_URL in docker-compose vs local development

## Development Workflows

### Local Development
```bash
# Environment setup (required)
cp .env.example .env  # Edit with your values

# Docker stack (recommended)
docker compose up --build

# Manual setup alternative
pip install -e .
uvicorn main:app --reload
```

### File Upload Integration
- Cloudinary integration in `src/services/cloudinary.py`
- Avatar uploads require multipart form data
- File validation in service layer, not at API level

### Testing/Debug Endpoints
- Health check: `GET /health`
- CORS test: `GET /cors-test` 
- API docs: `/docs` (Swagger UI)

## Database Conventions

### Model Relationships
- `User` has one-to-many `Contact` relationship
- Foreign key: `Contact.user_id → User.id`
- SQLAlchemy relationships: `User.contacts` and `Contact.owner`

### Migration Strategy
- Uses SQLAlchemy `Base.metadata.create_all()` in `main.py` (not Alembic currently)
- Models in `src/database/models.py` with proper indexing

## External Service Integrations

**Email Service**: SMTP configuration via environment variables
**Cloudinary**: Avatar/image uploads via `src/services/cloudinary.py`
**Redis**: Rate limiting backend (falls back to in-memory if unavailable)

## Common Pitfalls to Avoid

1. **Cross-user data exposure**: Always filter by `current_user.id`
2. **Missing rate limits**: Apply `@limiter.limit()` to sensitive endpoints
3. **Direct ORM usage**: Use repository pattern, not `db.query()` directly in API handlers
4. **Hardcoded secrets**: Use `settings` object from config, not environment variables directly
5. **Async/sync mixing**: Repository methods are `async`, but some operations are sync - follow existing patterns

When adding new features, follow the established layer separation and always implement proper user context isolation.