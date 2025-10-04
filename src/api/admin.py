"""Admin API endpoints for user and system management."""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from src.database.db import get_db
from src.database.models import User
from src.schemas import (
    AdminUserResponse,
    UserRoleUpdate,
    UserStatusUpdate,
    UserRoleEnum,
    AdminAction,
)
from src.services.admin import AdminService
from src.services.auth import get_current_admin
from src.services.rate_limiter import limiter

router = APIRouter()


@router.get("/users", response_model=Dict[str, Any])
@limiter.limit("10/minute")  # Rate limit admin operations
async def get_all_users(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(
        50, ge=1, le=100, description="Maximum number of users to return"
    ),
    role: Optional[UserRoleEnum] = Query(None, description="Filter by user role"),
    search: Optional[str] = Query(None, description="Search in username or email"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Get all users with filtering and pagination (Admin only).

    Allows admins to view all users in the system with optional filtering
    by role and search functionality.
    """
    try:
        admin_service = AdminService(db)

        role_filter = role.value if role else None
        result = await admin_service.get_all_users(
            skip=skip, limit=limit, role_filter=role_filter, search=search
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users: {str(e)}",
        )


@router.get("/users/{user_id}", response_model=AdminUserResponse)
@limiter.limit("20/minute")
async def get_user_details(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Get detailed information about a specific user (Admin only)."""
    try:
        admin_service = AdminService(db)
        user_details = await admin_service.get_user_details(user_id)

        if not user_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return user_details

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user details: {str(e)}",
        )


@router.put("/users/{user_id}/role", response_model=AdminUserResponse)
@limiter.limit("5/minute")  # Strict rate limit for role changes
async def update_user_role(
    request: Request,
    user_id: int,
    role_update: UserRoleUpdate,
    reason: Optional[str] = Query(None, description="Reason for role change"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Update user's role (Admin only).

    Changes a user's role with audit logging. Prevents admins from
    demoting themselves to maintain system security.
    """
    try:
        admin_service = AdminService(db)

        updated_user = await admin_service.update_user_role(
            user_id=user_id,
            new_role=role_update.role,
            admin_user=current_admin,
            reason=reason,
        )

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Return updated user details
        user_details = await admin_service.get_user_details(user_id)
        return user_details

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user role: {str(e)}",
        )


@router.put("/users/{user_id}/status", response_model=AdminUserResponse)
@limiter.limit("5/minute")  # Strict rate limit for status changes
async def update_user_status(
    request: Request,
    user_id: int,
    status_update: UserStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Update user's active status (Admin only).

    Activates or deactivates user accounts. Prevents admins from
    deactivating themselves.
    """
    try:
        admin_service = AdminService(db)

        updated_user = await admin_service.update_user_status(
            user_id=user_id, status_update=status_update, admin_user=current_admin
        )

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Return updated user details
        user_details = await admin_service.get_user_details(user_id)
        return user_details

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user status: {str(e)}",
        )


@router.delete("/users/{user_id}")
@limiter.limit("3/minute")  # Very strict rate limit for deletions
async def delete_user(
    request: Request,
    user_id: int,
    reason: Optional[str] = Query(None, description="Reason for deletion"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Delete a user account (Admin only).

    Permanently deletes a user account. Prevents deletion of admin users
    and self-deletion.
    """
    try:
        admin_service = AdminService(db)

        deleted = await admin_service.delete_user(
            user_id=user_id, admin_user=current_admin, reason=reason
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return {"message": f"User {user_id} has been deleted successfully"}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}",
        )


@router.get("/stats")
@limiter.limit("10/minute")
async def get_system_stats(
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Get system statistics (Admin only).

    Returns comprehensive system statistics including user counts,
    cache statistics, and system health information.
    """
    try:
        admin_service = AdminService(db)
        stats = await admin_service.get_system_stats()

        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve system stats: {str(e)}",
        )


@router.get("/users/by-role/{role}")
@limiter.limit("10/minute")
async def get_users_by_role(
    request: Request,
    role: UserRoleEnum,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Get users filtered by role (Admin only)."""
    try:
        admin_service = AdminService(db)

        result = await admin_service.get_all_users(
            skip=skip, limit=limit, role_filter=role.value
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users by role: {str(e)}",
        )
