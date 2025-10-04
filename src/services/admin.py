"""Admin service for administrative operations and user management."""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from src.database.models import User, UserRole
from src.repository.users import UserRepository
from src.schemas import UserRoleEnum, AdminUserResponse, UserStatusUpdate
from src.services.cache import cache_service

logger = logging.getLogger(__name__)


class AdminService:
    """Service class for administrative operations.

    Provides methods for managing users, roles, and system-wide operations
    that require elevated privileges.
    """

    def __init__(self, db: Session):
        self.db = db

    async def get_all_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role_filter: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get all users with optional filtering and pagination.

        Args:
            skip (int): Number of records to skip
            limit (int): Maximum number of records to return
            role_filter (Optional[str]): Filter by role
            search (Optional[str]): Search term for username/email

        Returns:
            Dict containing users list and metadata
        """
        try:
            if search:
                users = UserRepository.search_users(self.db, search, skip, limit)
                total = len(
                    UserRepository.search_users(self.db, search, 0, 1000)
                )  # Rough count
            elif role_filter:
                users = UserRepository.get_users_by_role(
                    self.db, role_filter, skip, limit
                )
                total = len(
                    UserRepository.get_users_by_role(self.db, role_filter, 0, 1000)
                )
            else:
                users = UserRepository.get_all_users(self.db, skip, limit)
                total = UserRepository.get_users_count(self.db)

            # Convert to admin response format
            users_data = [
                AdminUserResponse(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    full_name=user.full_name,
                    is_active=user.is_active,
                    is_verified=user.is_verified,
                    role=UserRoleEnum(user.role.value),
                    avatar_url=user.avatar_url,
                    created_at=None,  # Add if you have created_at field
                    last_login=None,  # Add if you have last_login field
                )
                for user in users
            ]

            return {
                "users": users_data,
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_next": (skip + limit) < total,
            }

        except Exception as e:
            logger.error(f"Failed to get users: {e}")
            raise

    async def update_user_role(
        self,
        user_id: int,
        new_role: UserRoleEnum,
        admin_user: User,
        reason: Optional[str] = None,
    ) -> Optional[User]:
        """Update user's role.

        Args:
            user_id (int): ID of user to update
            new_role (UserRoleEnum): New role to assign
            admin_user (User): Admin performing the action
            reason (Optional[str]): Reason for role change

        Returns:
            Optional[User]: Updated user or None if not found
        """
        try:
            # Prevent self-demotion from admin
            if user_id == admin_user.id and new_role != UserRoleEnum.ADMIN:
                raise ValueError("Admins cannot demote themselves")

            updated_user = UserRepository.update_user_role(
                self.db, user_id, new_role.value
            )

            if updated_user:
                # Log admin action
                logger.info(
                    f"Admin {admin_user.username} (ID: {admin_user.id}) changed user "
                    f"{updated_user.username} (ID: {user_id}) role to {new_role.value}. "
                    f"Reason: {reason or 'No reason provided'}"
                )

                # Cache admin action for audit
                cache_service.cache_admin_action(
                    admin_id=admin_user.id,
                    action=f"role_change_to_{new_role.value}",
                    target_user_id=user_id,
                    details=reason,
                )

                # Invalidate user cache and role cache
                cache_service.invalidate_user_cache(updated_user)
                cache_service.invalidate_user_role_cache(user_id)

            return updated_user

        except Exception as e:
            logger.error(f"Failed to update user role: {e}")
            raise

    async def update_user_status(
        self, user_id: int, status_update: UserStatusUpdate, admin_user: User
    ) -> Optional[User]:
        """Update user's active status.

        Args:
            user_id (int): ID of user to update
            status_update (UserStatusUpdate): Status update data
            admin_user (User): Admin performing the action

        Returns:
            Optional[User]: Updated user or None if not found
        """
        try:
            # Prevent self-deactivation
            if user_id == admin_user.id and not status_update.is_active:
                raise ValueError("Admins cannot deactivate themselves")

            updated_user = UserRepository.update_user_status(
                self.db, user_id, status_update.is_active
            )

            if updated_user:
                # Log admin action
                action = "activated" if status_update.is_active else "deactivated"
                logger.info(
                    f"Admin {admin_user.username} (ID: {admin_user.id}) {action} user "
                    f"{updated_user.username} (ID: {user_id}). "
                    f"Reason: {status_update.reason or 'No reason provided'}"
                )

                # Cache admin action for audit
                cache_service.cache_admin_action(
                    admin_id=admin_user.id,
                    action=f"user_{action}",
                    target_user_id=user_id,
                    details=status_update.reason,
                )

                # Invalidate user cache
                cache_service.invalidate_user_cache(updated_user)

            return updated_user

        except Exception as e:
            logger.error(f"Failed to update user status: {e}")
            raise

    async def get_user_details(self, user_id: int) -> Optional[AdminUserResponse]:
        """Get detailed user information for admin view.

        Args:
            user_id (int): ID of user to retrieve

        Returns:
            Optional[AdminUserResponse]: User details or None if not found
        """
        try:
            user = UserRepository.get_user_by_id(self.db, user_id)

            if not user:
                return None

            return AdminUserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                is_verified=user.is_verified,
                role=UserRoleEnum(user.role.value),
                avatar_url=user.avatar_url,
                created_at=None,  # Add if you have created_at field
                last_login=None,  # Add if you have last_login field
            )

        except Exception as e:
            logger.error(f"Failed to get user details: {e}")
            raise

    async def delete_user(
        self, user_id: int, admin_user: User, reason: Optional[str] = None
    ) -> bool:
        """Delete a user account (admin only).

        Args:
            user_id (int): ID of user to delete
            admin_user (User): Admin performing the action
            reason (Optional[str]): Reason for deletion

        Returns:
            bool: True if user was deleted, False otherwise
        """
        try:
            # Prevent self-deletion
            if user_id == admin_user.id:
                raise ValueError("Admins cannot delete themselves")

            user_to_delete = UserRepository.get_user_by_id(self.db, user_id)
            if not user_to_delete:
                return False

            # Don't allow deleting other admins unless super admin logic needed
            if user_to_delete.role == UserRole.ADMIN:
                raise ValueError("Cannot delete admin users")

            deleted = UserRepository.delete_user(self.db, user_id)

            if deleted:
                # Log admin action
                logger.warning(
                    f"Admin {admin_user.username} (ID: {admin_user.id}) deleted user "
                    f"{user_to_delete.username} (ID: {user_id}). "
                    f"Reason: {reason or 'No reason provided'}"
                )

                # Clear all caches for deleted user
                cache_service.clear_user_all_cache(user_id)

            return deleted

        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            raise

    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics for admin dashboard.

        Returns:
            Dict containing system statistics
        """
        try:
            total_users = UserRepository.get_users_count(self.db)
            admin_count = len(
                UserRepository.get_users_by_role(self.db, "admin", 0, 1000)
            )
            moderator_count = len(
                UserRepository.get_users_by_role(self.db, "moderator", 0, 1000)
            )
            user_count = len(UserRepository.get_users_by_role(self.db, "user", 0, 1000))

            # Get cache stats
            cache_stats = cache_service.get_cache_stats()

            return {
                "users": {
                    "total": total_users,
                    "admins": admin_count,
                    "moderators": moderator_count,
                    "regular_users": user_count,
                },
                "cache": cache_stats,
                "system": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": "operational",
                },
            }

        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            raise
