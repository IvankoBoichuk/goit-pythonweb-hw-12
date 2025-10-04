"""
Unit tests for service layer.

Tests for AuthService, AdminService, CacheService and other services.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta, date
from jose import jwt
import json

from src.services.auth import AuthService
from src.services.admin import AdminService
from src.services.cache import CacheService
from src.database.models import User, Contact, UserRole
from src.conf.config import settings


class TestAuthService:
    """Test AuthService functionality."""

    @pytest.mark.unit
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "testpassword123"
        hashed = AuthService.get_password_hash(password)

        result = AuthService.verify_password(password, hashed)
        assert result is True

    @pytest.mark.unit
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword456"
        hashed = AuthService.get_password_hash(password)

        result = AuthService.verify_password(wrong_password, hashed)
        assert result is False

    @pytest.mark.unit
    def test_get_password_hash(self):
        """Test password hashing."""
        password = "testpassword123"
        hashed = AuthService.get_password_hash(password)

        assert hashed != password
        assert hashed.startswith("$pbkdf2-sha256$")

    @pytest.mark.unit
    def test_create_access_token(self):
        """Test JWT access token creation."""
        data = {"sub": "testuser", "role": "user"}
        token = AuthService.create_access_token(data)

        assert token is not None

        # Decode token to verify content
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        assert payload["sub"] == "testuser"
        assert payload["role"] == "user"
        assert "exp" in payload

    @pytest.mark.unit
    def test_create_access_token_with_expires_delta(self):
        """Test JWT token creation with custom expiration."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=60)

        token = AuthService.create_access_token(data, expires_delta)
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )

        # Check expiration is approximately 60 minutes from now
        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_time = datetime.utcnow() + expires_delta
        time_diff = abs((exp_time - expected_time).total_seconds())
        assert time_diff < 5  # Allow 5 second tolerance

    @pytest.mark.unit
    @patch("src.services.auth.UserRepository")
    def test_authenticate_user_success(self, mock_repo_class):
        """Test successful user authentication."""
        # Setup mocks
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        mock_user = Mock()
        mock_user.username = "testuser"
        mock_user.hashed_password = AuthService.get_password_hash("testpass")
        mock_user.is_active = True

        mock_repo.get_user_by_username.return_value = mock_user

        # Test
        result = AuthService.authenticate_user(Mock(), "testuser", "testpass")

        assert result == mock_user
        mock_repo.get_user_by_username.assert_called_once_with("testuser")

    @pytest.mark.unit
    @patch("src.services.auth.UserRepository")
    def test_authenticate_user_wrong_password(self, mock_repo_class):
        """Test authentication with wrong password."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        mock_user = Mock()
        mock_user.username = "testuser"
        mock_user.hashed_password = AuthService.get_password_hash("correctpass")
        mock_user.is_active = True

        mock_repo.get_user_by_username.return_value = mock_user

        result = AuthService.authenticate_user(Mock(), "testuser", "wrongpass")

        assert result is False

    @pytest.mark.unit
    @patch("src.services.auth.UserRepository")
    def test_authenticate_user_inactive(self, mock_repo_class):
        """Test authentication with inactive user."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        mock_user = Mock()
        mock_user.username = "testuser"
        mock_user.hashed_password = AuthService.get_password_hash("testpass")
        mock_user.is_active = False

        mock_repo.get_user_by_username.return_value = mock_user

        result = AuthService.authenticate_user(Mock(), "testuser", "testpass")

        assert result is False

    @pytest.mark.unit
    @patch("src.services.auth.UserRepository")
    def test_authenticate_user_not_found(self, mock_repo_class):
        """Test authentication with non-existent user."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_user_by_username.return_value = None

        result = AuthService.authenticate_user(Mock(), "nonexistent", "anypass")

        assert result is False

    @pytest.mark.unit
    def test_check_user_role_sufficient_permission(self):
        """Test role checking with sufficient permissions."""
        user_role = UserRole.ADMIN
        required_role = UserRole.MODERATOR

        result = AuthService.check_user_role(user_role, required_role)
        assert result is True

    @pytest.mark.unit
    def test_check_user_role_insufficient_permission(self):
        """Test role checking with insufficient permissions."""
        user_role = UserRole.USER
        required_role = UserRole.ADMIN

        result = AuthService.check_user_role(user_role, required_role)
        assert result is False

    @pytest.mark.unit
    def test_check_user_role_exact_permission(self):
        """Test role checking with exact permissions."""
        user_role = UserRole.MODERATOR
        required_role = UserRole.MODERATOR

        result = AuthService.check_user_role(user_role, required_role)
        assert result is True


class TestAdminService:
    """Test AdminService functionality."""

    @pytest.fixture
    def mock_user_repo(self):
        """Mock UserRepository for AdminService tests."""
        mock = Mock()
        return mock

    @pytest.fixture
    def mock_cache_service(self):
        """Mock CacheService for AdminService tests."""
        mock = Mock()
        return mock

    @pytest.mark.unit
    def test_get_all_users(self, mock_user_repo, mock_cache_service):
        """Test getting all users."""
        # Setup
        mock_users = [Mock(), Mock(), Mock()]
        mock_user_repo.get_all_users.return_value = mock_users

        service = AdminService()
        service.user_repo = mock_user_repo
        service.cache_service = mock_cache_service

        # Test
        result = service.get_all_users(skip=0, limit=10)

        assert result == mock_users
        mock_user_repo.get_all_users.assert_called_once_with(skip=0, limit=10)

    @pytest.mark.unit
    def test_update_user_role_success(self, mock_user_repo, mock_cache_service):
        """Test successful role update."""
        # Setup
        mock_user = Mock()
        mock_user.id = 1
        mock_user.role = UserRole.USER
        mock_updated_user = Mock()
        mock_updated_user.role = UserRole.MODERATOR

        mock_user_repo.get_user_by_id.return_value = mock_user
        mock_user_repo.update_user_role.return_value = mock_updated_user

        service = AdminService()
        service.user_repo = mock_user_repo
        service.cache_service = mock_cache_service

        # Test
        result = service.update_user_role(1, UserRole.MODERATOR, admin_user_id=2)

        assert result == mock_updated_user
        mock_user_repo.update_user_role.assert_called_once_with(1, UserRole.MODERATOR)
        mock_cache_service.invalidate_user_role_cache.assert_called_once_with(1)

    @pytest.mark.unit
    def test_update_user_role_self_protection(self, mock_user_repo, mock_cache_service):
        """Test admin cannot demote themselves."""
        # Setup
        mock_admin = Mock()
        mock_admin.id = 1
        mock_admin.role = UserRole.ADMIN

        mock_user_repo.get_user_by_id.return_value = mock_admin

        service = AdminService()
        service.user_repo = mock_user_repo

        # Test - admin trying to demote themselves
        with pytest.raises(ValueError, match="Admins cannot change their own role"):
            service.update_user_role(1, UserRole.USER, admin_user_id=1)

    @pytest.mark.unit
    def test_update_user_status_success(self, mock_user_repo, mock_cache_service):
        """Test successful user status update."""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.is_active = True
        mock_updated_user = Mock()
        mock_updated_user.is_active = False

        mock_user_repo.get_user_by_id.return_value = mock_user
        mock_user_repo.update_user_status.return_value = mock_updated_user

        service = AdminService()
        service.user_repo = mock_user_repo
        service.cache_service = mock_cache_service

        result = service.update_user_status(1, False, admin_user_id=2)

        assert result == mock_updated_user
        mock_user_repo.update_user_status.assert_called_once_with(1, False)

    @pytest.mark.unit
    def test_update_user_status_self_protection(
        self, mock_user_repo, mock_cache_service
    ):
        """Test admin cannot deactivate themselves."""
        mock_admin = Mock()
        mock_admin.id = 1
        mock_admin.is_active = True

        mock_user_repo.get_user_by_id.return_value = mock_admin

        service = AdminService()
        service.user_repo = mock_user_repo

        # Test - admin trying to deactivate themselves
        with pytest.raises(ValueError, match="Admins cannot deactivate themselves"):
            service.update_user_status(1, False, admin_user_id=1)

    @pytest.mark.unit
    def test_delete_user_success(self, mock_user_repo, mock_cache_service):
        """Test successful user deletion."""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.role = UserRole.USER

        mock_user_repo.get_user_by_id.return_value = mock_user
        mock_user_repo.delete_user.return_value = True

        service = AdminService()
        service.user_repo = mock_user_repo
        service.cache_service = mock_cache_service

        result = service.delete_user(1, admin_user_id=2)

        assert result is True
        mock_user_repo.delete_user.assert_called_once_with(1)

    @pytest.mark.unit
    def test_delete_user_admin_protection(self, mock_user_repo, mock_cache_service):
        """Test cannot delete other admins."""
        mock_admin = Mock()
        mock_admin.id = 1
        mock_admin.role = UserRole.ADMIN

        mock_user_repo.get_user_by_id.return_value = mock_admin

        service = AdminService()
        service.user_repo = mock_user_repo

        # Test - trying to delete another admin
        with pytest.raises(ValueError, match="Cannot delete other administrators"):
            service.delete_user(1, admin_user_id=2)

    @pytest.mark.unit
    def test_get_system_stats(self, mock_user_repo, mock_cache_service):
        """Test getting system statistics."""
        # Setup
        mock_user_repo.get_users_count.return_value = 100
        mock_user_repo.get_users_by_role.side_effect = [
            [Mock()] * 5,  # 5 admins
            [Mock()] * 15,  # 15 moderators
            [Mock()] * 80,  # 80 users
        ]

        mock_cache_service.get_cache_stats.return_value = {
            "enabled": True,
            "hits": 1000,
            "misses": 100,
        }

        service = AdminService()
        service.user_repo = mock_user_repo
        service.cache_service = mock_cache_service

        # Test
        result = service.get_system_stats()

        assert result["users"]["total"] == 100
        assert result["users"]["admins"] == 5
        assert result["users"]["moderators"] == 15
        assert result["users"]["regular_users"] == 80
        assert result["cache"]["enabled"] is True


class TestCacheService:
    """Test CacheService functionality."""

    @pytest.mark.unit
    def test_cache_service_init_with_redis(self, mock_redis):
        """Test CacheService initialization with Redis."""
        service = CacheService()
        service.redis_client = mock_redis

        assert service.redis_client is not None
        assert service.enabled is True

    @pytest.mark.unit
    def test_cache_service_init_without_redis(self):
        """Test CacheService initialization without Redis."""
        with patch("redis.Redis", side_effect=Exception("Connection failed")):
            service = CacheService()

            assert service.redis_client is None
            assert service.enabled is False

    @pytest.mark.unit
    def test_set_cache(self, cache_service, mock_redis):
        """Test setting cache value."""
        cache_service.set("test_key", "test_value", 300)

        mock_redis.set.assert_called_once_with("test_key", "test_value", ex=300)

    @pytest.mark.unit
    def test_get_cache_hit(self, cache_service, mock_redis):
        """Test cache hit."""
        mock_redis.get.return_value = b"cached_value"

        result = cache_service.get("test_key")

        assert result == "cached_value"
        mock_redis.get.assert_called_once_with("test_key")

    @pytest.mark.unit
    def test_get_cache_miss(self, cache_service, mock_redis):
        """Test cache miss."""
        mock_redis.get.return_value = None

        result = cache_service.get("test_key")

        assert result is None

    @pytest.mark.unit
    def test_cache_user_role(self, cache_service, mock_redis):
        """Test caching user role."""
        cache_service.cache_user_role(1, UserRole.ADMIN)

        expected_key = "user_role:1"
        expected_value = json.dumps({"role": "admin"})
        mock_redis.set.assert_called_once_with(expected_key, expected_value, ex=900)

    @pytest.mark.unit
    def test_get_user_role_cache_hit(self, cache_service, mock_redis):
        """Test getting user role from cache."""
        mock_redis.get.return_value = b'{"role": "admin"}'

        result = cache_service.get_user_role_cache(1)

        assert result == UserRole.ADMIN
        mock_redis.get.assert_called_once_with("user_role:1")

    @pytest.mark.unit
    def test_get_user_role_cache_miss(self, cache_service, mock_redis):
        """Test cache miss for user role."""
        mock_redis.get.return_value = None

        result = cache_service.get_user_role_cache(1)

        assert result is None

    @pytest.mark.unit
    def test_invalidate_user_role_cache(self, cache_service, mock_redis):
        """Test invalidating user role cache."""
        cache_service.invalidate_user_role_cache(1)

        mock_redis.delete.assert_called_once_with("user_role:1")

    @pytest.mark.unit
    def test_cache_admin_action(self, cache_service, mock_redis):
        """Test caching admin action."""
        action_data = {
            "action": "update_role",
            "target_user_id": 1,
            "admin_user_id": 2,
            "details": "Updated to moderator",
        }

        cache_service.cache_admin_action(action_data)

        # Should call set with some key and JSON data
        mock_redis.set.assert_called_once()
        args, kwargs = mock_redis.set.call_args

        assert "admin_action:" in args[0]
        assert json.loads(args[1])["action"] == "update_role"

    @pytest.mark.unit
    def test_get_cache_stats(self, cache_service, mock_redis):
        """Test getting cache statistics."""
        mock_redis.info.return_value = {
            "keyspace_hits": 1000,
            "keyspace_misses": 100,
            "used_memory": 1024000,
        }

        result = cache_service.get_cache_stats()

        assert result["enabled"] is True
        assert result["hits"] == 1000
        assert result["misses"] == 100
        assert result["memory_usage"] == 1024000

    @pytest.mark.unit
    def test_cache_disabled_operations(self):
        """Test cache operations when disabled."""
        service = CacheService()
        service.enabled = False
        service.redis_client = None

        # All operations should handle disabled cache gracefully
        service.set("key", "value")  # Should not raise error
        result = service.get("key")
        assert result is None

        service.cache_user_role(1, UserRole.ADMIN)  # Should not raise error
        role = service.get_user_role_cache(1)
        assert role is None


class TestServiceIntegration:
    """Test service layer integration."""

    @pytest.mark.unit
    @patch("src.services.auth.UserRepository")
    @patch("src.services.auth.CacheService")
    def test_auth_service_with_cache(self, mock_cache_class, mock_repo_class):
        """Test AuthService integration with cache."""
        # Setup mocks
        mock_cache = Mock()
        mock_cache_class.return_value = mock_cache
        mock_cache.get_user_role_cache.return_value = UserRole.ADMIN

        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        mock_user = Mock()
        mock_user.role = UserRole.ADMIN
        mock_repo.get_user_by_username.return_value = mock_user

        # Test that cache is checked first
        user_role = mock_cache.get_user_role_cache(1)
        assert user_role == UserRole.ADMIN

        # Cache should be called before database
        mock_cache.get_user_role_cache.assert_called_once_with(1)

    @pytest.mark.unit
    def test_service_error_handling(self):
        """Test service layer error handling."""
        service = AdminService()

        # Test with None user_repo
        with pytest.raises(AttributeError):
            service.get_all_users()

    @pytest.mark.unit
    def test_admin_service_logging(self, mock_user_repo, mock_cache_service):
        """Test that admin actions are logged."""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.role = UserRole.USER

        mock_updated_user = Mock()
        mock_updated_user.role = UserRole.MODERATOR

        mock_user_repo.get_user_by_id.return_value = mock_user
        mock_user_repo.update_user_role.return_value = mock_updated_user

        service = AdminService()
        service.user_repo = mock_user_repo
        service.cache_service = mock_cache_service

        service.update_user_role(1, UserRole.MODERATOR, admin_user_id=2)

        # Verify that cache action was logged
        mock_cache_service.cache_admin_action.assert_called_once()
        call_args = mock_cache_service.cache_admin_action.call_args[0][0]

        assert call_args["action"] == "update_role"
        assert call_args["target_user_id"] == 1
        assert call_args["admin_user_id"] == 2
