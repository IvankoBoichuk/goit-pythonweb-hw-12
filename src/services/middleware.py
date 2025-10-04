"""Role-based middleware for automatic role checking and admin action logging."""

import logging
import time
from typing import Callable
from fastapi import Request, Response
from fastapi.routing import APIRoute

from src.services.cache import cache_service

logger = logging.getLogger(__name__)


class AdminActionLoggingRoute(APIRoute):
    """Custom route class for logging admin actions."""

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def admin_logging_route_handler(request: Request) -> Response:
            # Check if this is an admin endpoint
            if "/api/admin" in str(request.url):
                start_time = time.time()

                try:
                    # Get user info if available (will be set by auth dependency)
                    user_id = getattr(request.state, "user_id", None)
                    username = getattr(request.state, "username", None)

                    # Execute the original handler
                    response = await original_route_handler(request)

                    # Log successful admin action
                    process_time = time.time() - start_time

                    logger.info(
                        f"Admin action: {request.method} {request.url.path} "
                        f"by user {username} (ID: {user_id}) - "
                        f"Status: {response.status_code} - "
                        f"Time: {process_time:.4f}s"
                    )

                    # Cache successful admin actions for audit
                    if user_id and 200 <= response.status_code < 300:
                        cache_service.cache_admin_action(
                            admin_id=user_id,
                            action=f"{request.method}_{request.url.path}",
                            target_user_id=0,  # Will be overridden by specific endpoints
                            details=f"HTTP {response.status_code} in {process_time:.4f}s",
                        )

                    return response

                except Exception as e:
                    # Log failed admin action
                    process_time = time.time() - start_time

                    logger.error(
                        f"Failed admin action: {request.method} {request.url.path} - "
                        f"Error: {str(e)} - Time: {process_time:.4f}s"
                    )

                    raise
            else:
                # Non-admin endpoint, use original handler
                return await original_route_handler(request)

        return admin_logging_route_handler


async def role_enforcement_middleware(request: Request, call_next):
    """Middleware for enforcing role-based access and logging.

    This middleware runs before route handlers and can perform
    additional security checks or logging.
    """
    start_time = time.time()

    try:
        # Execute the request
        response = await call_next(request)

        # Log admin endpoint access
        if "/api/admin" in str(request.url):
            process_time = time.time() - start_time

            logger.info(
                f"Admin endpoint accessed: {request.method} {request.url.path} - "
                f"Status: {response.status_code} - Time: {process_time:.4f}s"
            )

        return response

    except Exception as e:
        process_time = time.time() - start_time

        logger.error(
            f"Request failed: {request.method} {request.url.path} - "
            f"Error: {str(e)} - Time: {process_time:.4f}s"
        )

        raise


async def user_context_middleware(request: Request, call_next):
    """Middleware to set user context for logging purposes.

    This middleware attempts to extract user information from
    the authorization header and set it in request.state for
    later use in logging.
    """
    try:
        # Try to extract user info from authorization header
        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

            # We could decode JWT here, but it's better to let
            # the auth dependency handle it properly
            # This is just for setting context for logging

            # Set a flag that we have auth info
            request.state.has_auth = True
        else:
            request.state.has_auth = False

        response = await call_next(request)
        return response

    except Exception as e:
        logger.error(f"User context middleware error: {e}")
        # Continue processing even if middleware fails
        response = await call_next(request)
        return response


class RoleBasedRateLimitingMiddleware:
    """Middleware for applying different rate limits based on user roles."""

    def __init__(self, default_limit: int = 100, admin_limit: int = 500):
        self.default_limit = default_limit
        self.admin_limit = admin_limit

    async def __call__(self, request: Request, call_next):
        """Apply role-based rate limiting."""
        try:
            # Get user role from cache if available
            user_id = getattr(request.state, "user_id", None)

            if user_id:
                cached_role = cache_service.get_user_role_cache(user_id)

                # Apply different limits based on role
                if cached_role == "admin":
                    # Admins get higher limits
                    request.state.rate_limit = self.admin_limit
                else:
                    request.state.rate_limit = self.default_limit
            else:
                request.state.rate_limit = self.default_limit

            response = await call_next(request)
            return response

        except Exception as e:
            logger.error(f"Role-based rate limiting middleware error: {e}")
            response = await call_next(request)
            return response


def setup_role_middleware(app):
    """Setup role-based middleware for the FastAPI app.

    Args:
        app: FastAPI application instance
    """
    # Add middlewares in reverse order (they're executed in LIFO)

    # 1. User context middleware (runs first)
    app.middleware("http")(user_context_middleware)

    # 2. Role enforcement middleware
    app.middleware("http")(role_enforcement_middleware)

    logger.info("Role-based middleware setup completed")
