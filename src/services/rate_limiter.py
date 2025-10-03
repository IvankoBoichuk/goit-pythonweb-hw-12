from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from src.conf.config import settings
import redis
import logging

logger = logging.getLogger(__name__)

# Simple in-memory storage for development (if Redis is not available)
class InMemoryStorage:
    def __init__(self):
        self.storage = {}
    
    def get(self, key):
        return self.storage.get(key)
    
    def set(self, key, value, ex=None):
        self.storage[key] = value
        return True
    
    def delete(self, key):
        if key in self.storage:
            del self.storage[key]
        return True

# Try to connect to Redis, fallback to in-memory storage
try:
    if settings.rate_limit_enabled:
        # Try Redis connection
        redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        redis_client.ping()  # Test connection
        storage = redis_client
        logger.info("Connected to Redis for rate limiting")
    else:
        storage = InMemoryStorage()
        logger.info("Rate limiting disabled")
except (redis.ConnectionError, redis.TimeoutError):
    logger.warning("Redis not available, using in-memory storage for rate limiting")
    storage = InMemoryStorage()

# Rate limiter key function - use user ID if authenticated, otherwise IP
def get_user_id(request: Request):
    """Get user identifier for rate limiting."""
    # Try to get user from request state (if authenticated)
    user = getattr(request.state, 'user', None)
    if user and hasattr(user, 'id'):
        return f"user:{user.id}"
    
    # Fallback to IP address
    return get_remote_address(request)

# Create limiter instance
limiter = Limiter(
    key_func=get_user_id,
    storage_uri=settings.redis_url if settings.rate_limit_enabled else "memory://",
    default_limits=["200/day", "50/hour"]  # Default limits for all endpoints
)

# Custom rate limit exceeded handler
def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded."""
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Limit: {exc.detail}",
            "retry_after": exc.retry_after
        },
        headers={"Retry-After": str(exc.retry_after)}
    )