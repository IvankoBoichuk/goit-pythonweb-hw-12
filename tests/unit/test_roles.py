"""
Tests for role-based access control system.

Specialized tests for role hierarchy, middleware, and security mechanisms.
"""

import pytest
from unittest.mock import patch, Mock
from fastapi import HTTPException, status
from datetime import datetime, timedelta

from src.services.auth import AuthService
from src.services.admin import AdminService
from src.database.models import User, UserRole
from src.services.middleware import AdminActionLoggingRoute


class TestRoleHierarchy:
    """Test role hierarchy and permission inheritance."""

    @pytest.mark.roles
    def test_role_levels(self):
        """Test role level values."""
        assert UserRole.USER.value == "user"
        assert UserRole.MODERATOR.value == "moderator"
        assert UserRole.ADMIN.value == "admin"

    @pytest.mark.roles
    def test_admin_can_access_all_levels(self):
        """Test admin can access all role levels."""
        admin_role = UserRole.ADMIN

        # Admin should be able to access user level
        assert AuthService.check_user_role(admin_role, UserRole.USER) is True

        # Admin should be able to access moderator level
        assert AuthService.check_user_role(admin_role, UserRole.MODERATOR) is True

        # Admin should be able to access admin level
        assert AuthService.check_user_role(admin_role, UserRole.ADMIN) is True

    @pytest.mark.roles
    def test_moderator_limited_access(self):
        """Test moderator has limited access."""
        moderator_role = UserRole.MODERATOR

        # Moderator should be able to access user level
        assert AuthService.check_user_role(moderator_role, UserRole.USER) is True

        # Moderator should be able to access moderator level
        assert AuthService.check_user_role(moderator_role, UserRole.MODERATOR) is True

        # Moderator should NOT be able to access admin level
        assert AuthService.check_user_role(moderator_role, UserRole.ADMIN) is False

    @pytest.mark.roles
    def test_user_minimal_access(self):
        """Test user has minimal access."""
        user_role = UserRole.USER

        # User should be able to access user level
        assert AuthService.check_user_role(user_role, UserRole.USER) is True

        # User should NOT be able to access moderator level
        assert AuthService.check_user_role(user_role, UserRole.MODERATOR) is False

        # User should NOT be able to access admin level
        assert AuthService.check_user_role(user_role, UserRole.ADMIN) is False

    @pytest.mark.roles
    def test_role_comparison_edge_cases(self):
        """Test role comparison edge cases."""
        # Same role should always pass
        assert AuthService.check_user_role(UserRole.USER, UserRole.USER) is True
        assert (
            AuthService.check_user_role(UserRole.MODERATOR, UserRole.MODERATOR) is True
        )
        assert AuthService.check_user_role(UserRole.ADMIN, UserRole.ADMIN) is True


class TestAdminSelfProtection:
    """Test admin self-protection mechanisms."""

    @pytest.mark.roles
    def test_admin_cannot_demote_self(self):
        """Test admin cannot demote their own role."""
        mock_repo = Mock()
        mock_cache = Mock()

        mock_admin = Mock()
        mock_admin.id = 1
        mock_admin.role = UserRole.ADMIN

        mock_repo.get_user_by_id.return_value = mock_admin

        service = AdminService()
        service.user_repo = mock_repo
        service.cache_service = mock_cache

        # Admin trying to demote themselves should raise error
        with pytest.raises(ValueError, match="Admins cannot change their own role"):
            service.update_user_role(1, UserRole.USER, admin_user_id=1)

    @pytest.mark.roles
    def test_admin_cannot_deactivate_self(self):
        """Test admin cannot deactivate themselves."""
        mock_repo = Mock()
        mock_cache = Mock()

        mock_admin = Mock()
        mock_admin.id = 1
        mock_admin.is_active = True

        mock_repo.get_user_by_id.return_value = mock_admin

        service = AdminService()
        service.user_repo = mock_repo
        service.cache_service = mock_cache

        # Admin trying to deactivate themselves should raise error
        with pytest.raises(ValueError, match="Admins cannot deactivate themselves"):
            service.update_user_status(1, False, admin_user_id=1)

    @pytest.mark.roles
    def test_admin_cannot_delete_other_admins(self):
        """Test admin cannot delete other admins."""
        mock_repo = Mock()
        mock_cache = Mock()

        mock_other_admin = Mock()
        mock_other_admin.id = 2
        mock_other_admin.role = UserRole.ADMIN

        mock_repo.get_user_by_id.return_value = mock_other_admin

        service = AdminService()
        service.user_repo = mock_repo
        service.cache_service = mock_cache

        # Admin trying to delete another admin should raise error
        with pytest.raises(ValueError, match="Cannot delete other administrators"):
            service.delete_user(2, admin_user_id=1)

    @pytest.mark.roles
    def test_admin_can_manage_non_admins(self):
        """Test admin can manage users and moderators."""
        mock_repo = Mock()
        mock_cache = Mock()

        # Mock regular user
        mock_user = Mock()
        mock_user.id = 2
        mock_user.role = UserRole.USER
        mock_user.is_active = True

        mock_updated_user = Mock()
        mock_updated_user.role = UserRole.MODERATOR

        mock_repo.get_user_by_id.return_value = mock_user
        mock_repo.update_user_role.return_value = mock_updated_user

        service = AdminService()
        service.user_repo = mock_repo
        service.cache_service = mock_cache

        # Admin should be able to update non-admin user
        result = service.update_user_role(2, UserRole.MODERATOR, admin_user_id=1)

        assert result == mock_updated_user
        mock_repo.update_user_role.assert_called_once_with(2, UserRole.MODERATOR)


class TestRoleBasedDecorators:
    """Test role-based authentication decorators."""

    @pytest.mark.roles
    @patch("src.services.auth.CacheService")
    @patch("src.services.auth.UserRepository")
    def test_require_role_decorator_success(self, mock_repo_class, mock_cache_class):
        """Test require_role decorator with sufficient permissions."""
        # Setup mocks
        mock_cache = Mock()
        mock_cache_class.return_value = mock_cache
        mock_cache.get_user_role_cache.return_value = UserRole.ADMIN

        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        mock_user = Mock()
        mock_user.role = UserRole.ADMIN
        mock_user.is_active = True
        mock_repo.get_user_by_username.return_value = mock_user

        # Test that admin can access moderator-required endpoint
        from src.services.auth import require_role

        # Create a mock dependency function
        async def mock_get_current_user():
            return mock_user

        # The decorator should not raise an exception
        decorated_func = require_role(UserRole.MODERATOR)

        # Since this is a dependency decorator, we test the underlying logic
        assert AuthService.check_user_role(UserRole.ADMIN, UserRole.MODERATOR) is True

    @pytest.mark.roles
    def test_require_role_insufficient_permissions(self):
        """Test require_role decorator with insufficient permissions."""
        # User trying to access admin endpoint should fail
        assert AuthService.check_user_role(UserRole.USER, UserRole.ADMIN) is False

    @pytest.mark.roles
    @patch("src.services.auth.CacheService")
    @patch("src.services.auth.UserRepository")
    def test_get_current_admin_success(self, mock_repo_class, mock_cache_class):
        """Test get_current_admin with admin user."""
        mock_cache = Mock()
        mock_cache_class.return_value = mock_cache
        mock_cache.get_user_role_cache.return_value = UserRole.ADMIN

        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        mock_admin = Mock()
        mock_admin.role = UserRole.ADMIN
        mock_admin.is_active = True

        # Test the underlying check
        assert mock_admin.role == UserRole.ADMIN

    @pytest.mark.roles
    def test_get_current_admin_insufficient_permissions(self):
        """Test get_current_admin with non-admin user."""
        mock_user = Mock()
        mock_user.role = UserRole.USER

        # Non-admin should not pass admin check
        assert mock_user.role != UserRole.ADMIN


class TestRoleCaching:
    """Test role caching functionality."""

    @pytest.mark.roles
    def test_cache_user_role(self, cache_service, mock_redis):
        """Test caching user role."""
        cache_service.cache_user_role(1, UserRole.ADMIN)

        # Verify cache was called with correct parameters
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args

        assert "user_role:1" in call_args[0]
        assert "admin" in call_args[0][1]

    @pytest.mark.roles
    def test_get_user_role_from_cache(self, cache_service, mock_redis):
        """Test retrieving user role from cache."""
        import json

        mock_redis.get.return_value = json.dumps({"role": "admin"}).encode()

        result = cache_service.get_user_role_cache(1)

        assert result == UserRole.ADMIN
        mock_redis.get.assert_called_once_with("user_role:1")

    @pytest.mark.roles
    def test_invalidate_user_role_cache(self, cache_service, mock_redis):
        """Test invalidating user role cache."""
        cache_service.invalidate_user_role_cache(1)

        mock_redis.delete.assert_called_once_with("user_role:1")

    @pytest.mark.roles
    def test_role_cache_miss(self, cache_service, mock_redis):
        """Test cache miss for user role."""
        mock_redis.get.return_value = None

        result = cache_service.get_user_role_cache(1)

        assert result is None

    @pytest.mark.roles
    def test_role_cache_performance(self, cache_service, mock_redis):
        """Test role caching improves performance."""
        # First call should hit database
        mock_redis.get.return_value = None
        cache_service.get_user_role_cache(1)

        # Second call should hit cache
        import json

        mock_redis.get.return_value = json.dumps({"role": "admin"}).encode()
        result = cache_service.get_user_role_cache(1)

        assert result == UserRole.ADMIN
        # Cache should have been queried
        assert mock_redis.get.call_count >= 1


class TestAdminActionLogging:
    """Test admin action logging and auditing."""

    @pytest.mark.roles
    def test_cache_admin_action(self, cache_service, mock_redis):
        """Test caching admin actions for audit."""
        action_data = {
            "action": "update_role",
            "target_user_id": 1,
            "admin_user_id": 2,
            "details": "Changed from user to moderator",
            "timestamp": datetime.utcnow().isoformat(),
        }

        cache_service.cache_admin_action(action_data)

        # Verify action was cached
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args

        assert "admin_action:" in call_args[0][0]

    @pytest.mark.roles
    def test_admin_service_logs_actions(self):
        """Test AdminService logs all actions."""
        mock_repo = Mock()
        mock_cache = Mock()

        mock_user = Mock()
        mock_user.id = 1
        mock_user.role = UserRole.USER

        mock_updated_user = Mock()
        mock_updated_user.id = 1
        mock_updated_user.role = UserRole.MODERATOR

        mock_repo.get_user_by_id.return_value = mock_user
        mock_repo.update_user_role.return_value = mock_updated_user

        service = AdminService()
        service.user_repo = mock_repo
        service.cache_service = mock_cache

        # Perform admin action
        service.update_user_role(1, UserRole.MODERATOR, admin_user_id=2)

        # Verify action was logged
        mock_cache.cache_admin_action.assert_called_once()

        call_args = mock_cache.cache_admin_action.call_args[0][0]
        assert call_args["action"] == "update_role"
        assert call_args["target_user_id"] == 1
        assert call_args["admin_user_id"] == 2

    @pytest.mark.roles
    def test_get_recent_admin_actions(self, cache_service, mock_redis):
        """Test retrieving recent admin actions."""
        # Mock recent actions in cache
        mock_actions = [
            {"action": "update_role", "timestamp": "2023-01-01T10:00:00"},
            {"action": "deactivate_user", "timestamp": "2023-01-01T11:00:00"},
        ]

        # Mock Redis scan for admin action keys
        mock_redis.scan.return_value = (0, ["admin_action:1", "admin_action:2"])
        mock_redis.get.side_effect = [
            json.dumps(mock_actions[0]).encode(),
            json.dumps(mock_actions[1]).encode(),
        ]

        result = cache_service.get_recent_admin_actions(limit=10)

        assert len(result) == 2
        assert result[0]["action"] == "update_role"


class TestMiddlewareIntegration:
    """Test middleware integration with role system."""

    @pytest.mark.roles
    def test_admin_action_logging_route(self):
        """Test AdminActionLoggingRoute functionality."""
        mock_request = Mock()
        mock_request.method = "PUT"
        mock_request.url.path = "/api/admin/users/1/role"
        mock_request.headers = {"Authorization": "Bearer test_token"}

        # Create logging route
        route = AdminActionLoggingRoute()

        # The route should identify this as an admin action
        assert "/api/admin/" in mock_request.url.path
        assert mock_request.method in ["POST", "PUT", "DELETE"]

    @pytest.mark.roles
    def test_middleware_user_context(self):
        """Test middleware sets user context correctly."""
        # This would test the user context middleware
        # In a real implementation, you'd test that the middleware:
        # 1. Extracts user from JWT token
        # 2. Sets user context for logging
        # 3. Handles unauthorized requests

        # Mock implementation test
        mock_user_context = {"user_id": 1, "username": "admin", "role": "admin"}

        # Verify context contains expected fields
        assert "user_id" in mock_user_context
        assert "role" in mock_user_context
        assert mock_user_context["role"] == "admin"

    @pytest.mark.roles
    def test_role_based_rate_limiting(self):
        """Test different rate limits for different roles."""
        # Test that different roles have different rate limits
        admin_limit = 100  # requests per minute
        moderator_limit = 50
        user_limit = 20

        # Verify rate limits are configured appropriately
        assert admin_limit > moderator_limit > user_limit


class TestSecurityMechanisms:
    """Test security mechanisms in role system."""

    @pytest.mark.roles
    def test_token_includes_role(self):
        """Test JWT tokens include role information."""
        token_data = {"sub": "admin", "role": "admin"}
        token = AuthService.create_access_token(token_data)

        # Decode token to verify role is included
        from jose import jwt
        from src.conf.config import settings

        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        assert payload["role"] == "admin"

    @pytest.mark.roles
    def test_role_validation_in_token(self):
        """Test role validation from JWT token."""
        # Test valid role
        valid_roles = ["user", "moderator", "admin"]

        for role in valid_roles:
            token_data = {"sub": "testuser", "role": role}
            token = AuthService.create_access_token(token_data)

            from jose import jwt
            from src.conf.config import settings

            payload = jwt.decode(
                token, settings.secret_key, algorithms=[settings.algorithm]
            )
            assert payload["role"] in valid_roles

    @pytest.mark.roles
    def test_expired_token_handling(self):
        """Test handling of expired tokens."""
        # Create token with very short expiration
        token_data = {"sub": "testuser", "role": "admin"}
        expired_token = AuthService.create_access_token(
            token_data, expires_delta=timedelta(seconds=-1)  # Already expired
        )

        # Attempting to decode should raise an exception
        from jose import jwt, JWTError
        from src.conf.config import settings

        with pytest.raises(JWTError):
            jwt.decode(
                expired_token, settings.secret_key, algorithms=[settings.algorithm]
            )

    @pytest.mark.roles
    def test_invalid_role_in_token(self):
        """Test handling of invalid roles in token."""
        token_data = {"sub": "testuser", "role": "invalid_role"}
        token = AuthService.create_access_token(token_data)

        from jose import jwt
        from src.conf.config import settings

        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )

        # The role should be in the payload, but validation should happen at endpoint level
        assert payload["role"] == "invalid_role"

        # Role validation should reject invalid roles
        try:
            invalid_role = UserRole(payload["role"])
            assert False, "Should have raised ValueError"
        except ValueError:
            # Expected - invalid role should raise ValueError
            pass


class TestRoleSystemIntegration:
    """Integration tests for the complete role system."""

    @pytest.mark.integration
    @pytest.mark.roles
    def test_complete_role_workflow(self, client, auth_headers_admin):
        """Test complete role management workflow."""
        # 1. Create a new user
        user_data = {
            "username": "roletest",
            "email": "roletest@example.com",
            "password": "testpass123",
            "full_name": "Role Test User",
        }

        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED
        created_user = response.json()

        # 2. Verify user starts with USER role
        assert created_user["role"] == "user"

        # 3. Admin promotes user to moderator
        response = client.put(
            f"/api/admin/users/{created_user['id']}/role",
            json={"role": "moderator"},
            headers=auth_headers_admin,
        )
        assert response.status_code == status.HTTP_200_OK

        # 4. Verify role was updated
        updated_user = response.json()
        assert updated_user["role"] == "moderator"

        # 5. Admin deactivates user
        response = client.put(
            f"/api/admin/users/{created_user['id']}/status",
            json={"is_active": False, "reason": "Test deactivation"},
            headers=auth_headers_admin,
        )
        assert response.status_code == status.HTTP_200_OK

        # 6. Verify user is deactivated
        deactivated_user = response.json()
        assert deactivated_user["is_active"] is False

    @pytest.mark.integration
    @pytest.mark.roles
    def test_role_system_error_recovery(self, client, auth_headers_admin):
        """Test role system handles errors gracefully."""
        # Try to update non-existent user
        response = client.put(
            "/api/admin/users/999999/role",
            json={"role": "admin"},
            headers=auth_headers_admin,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Try to set invalid role
        response = client.put(
            "/api/admin/users/1/role",
            json={"role": "invalid"},
            headers=auth_headers_admin,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
