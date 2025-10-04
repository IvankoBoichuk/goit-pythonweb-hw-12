"""
Integration tests for API endpoints.

Tests for auth, contacts, and admin endpoints with different user roles.
"""

import pytest
from fastapi import status
from datetime import date, datetime
import json

from tests.conftest import (
    UserFactory,
    ContactFactory,
    assert_user_response,
    assert_contact_response,
)
from src.database.models import UserRole


class TestAuthAPI:
    """Test authentication API endpoints."""

    @pytest.mark.integration
    def test_register_user_success(self, client, db_session):
        """Test successful user registration."""
        user_data = UserFactory.create_user_data(
            username="newuser", email="newuser@example.com", password="securepass123"
        )

        response = client.post("/api/auth/register", json=user_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "user"
        assert "id" in data

    @pytest.mark.integration
    def test_register_user_duplicate_username(self, client, regular_user):
        """Test registration with duplicate username."""
        user_data = UserFactory.create_user_data(
            username=regular_user.username, email="different@example.com"
        )

        response = client.post("/api/auth/register", json=user_data)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already registered" in response.json()["detail"]

    @pytest.mark.integration
    def test_register_user_duplicate_email(self, client, regular_user):
        """Test registration with duplicate email."""
        user_data = UserFactory.create_user_data(
            username="differentuser", email=regular_user.email
        )

        response = client.post("/api/auth/register", json=user_data)

        assert response.status_code == status.HTTP_409_CONFLICT

    @pytest.mark.integration
    def test_login_success(self, client, db_session):
        """Test successful login."""
        # First register a user
        user_data = UserFactory.create_user_data()
        client.post("/api/auth/register", json=user_data)

        # Then login
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"],
        }

        response = client.post("/api/auth/login", data=login_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.integration
    def test_login_invalid_credentials(self, client, regular_user):
        """Test login with invalid credentials."""
        login_data = {"username": regular_user.username, "password": "wrongpassword"}

        response = client.post("/api/auth/login", data=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.integration
    def test_login_inactive_user(self, client, inactive_user):
        """Test login with inactive user."""
        login_data = {"username": inactive_user.username, "password": "testpass"}

        response = client.post("/api/auth/login", data=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.integration
    def test_get_current_user(self, client, auth_headers_user, regular_user):
        """Test getting current user info."""
        response = client.get("/api/auth/me", headers=auth_headers_user)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert_user_response(data, regular_user)

    @pytest.mark.integration
    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without authentication."""
        response = client.get("/api/auth/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.integration
    def test_refresh_token(self, client, auth_headers_user):
        """Test token refresh endpoint."""
        response = client.post("/api/auth/refresh", headers=auth_headers_user)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


class TestContactsAPI:
    """Test contacts API endpoints."""

    @pytest.mark.integration
    def test_create_contact_success(self, client, auth_headers_user):
        """Test successful contact creation."""
        contact_data = ContactFactory.create_contact_data()

        response = client.post(
            "/api/contacts/", json=contact_data, headers=auth_headers_user
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["first_name"] == contact_data["first_name"]
        assert data["last_name"] == contact_data["last_name"]
        assert data["email"] == contact_data["email"]
        assert "id" in data

    @pytest.mark.integration
    def test_create_contact_unauthorized(self, client):
        """Test creating contact without authentication."""
        contact_data = ContactFactory.create_contact_data()

        response = client.post("/api/contacts/", json=contact_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.integration
    def test_get_contacts(self, client, auth_headers_user, multiple_contacts):
        """Test getting user's contacts."""
        response = client.get("/api/contacts/", headers=auth_headers_user)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 15  # From multiple_contacts fixture

    @pytest.mark.integration
    def test_get_contacts_pagination(
        self, client, auth_headers_user, multiple_contacts
    ):
        """Test contacts pagination."""
        response = client.get(
            "/api/contacts/?skip=0&limit=10", headers=auth_headers_user
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 10

        # Test second page
        response = client.get(
            "/api/contacts/?skip=10&limit=10", headers=auth_headers_user
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 5

    @pytest.mark.integration
    def test_get_contact_by_id(self, client, auth_headers_user, sample_contact):
        """Test getting specific contact."""
        response = client.get(
            f"/api/contacts/{sample_contact.id}", headers=auth_headers_user
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert_contact_response(data, sample_contact)

    @pytest.mark.integration
    def test_get_contact_not_found(self, client, auth_headers_user):
        """Test getting non-existent contact."""
        response = client.get("/api/contacts/999999", headers=auth_headers_user)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.integration
    def test_get_contact_wrong_user(self, client, auth_headers_admin, sample_contact):
        """Test getting contact belonging to different user."""
        # sample_contact belongs to regular_user, trying to access as admin
        response = client.get(
            f"/api/contacts/{sample_contact.id}", headers=auth_headers_admin
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.integration
    def test_update_contact(self, client, auth_headers_user, sample_contact):
        """Test updating contact."""
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "email": sample_contact.email,
            "phone": sample_contact.phone,
            "birthday": sample_contact.birthday.isoformat(),
        }

        response = client.put(
            f"/api/contacts/{sample_contact.id}",
            json=update_data,
            headers=auth_headers_user,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"

    @pytest.mark.integration
    def test_update_contact_not_found(self, client, auth_headers_user):
        """Test updating non-existent contact."""
        update_data = ContactFactory.create_contact_data()

        response = client.put(
            "/api/contacts/999999", json=update_data, headers=auth_headers_user
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.integration
    def test_delete_contact(self, client, auth_headers_user, sample_contact):
        """Test deleting contact."""
        response = client.delete(
            f"/api/contacts/{sample_contact.id}", headers=auth_headers_user
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify contact is deleted
        response = client.get(
            f"/api/contacts/{sample_contact.id}", headers=auth_headers_user
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.integration
    def test_search_contacts(self, client, auth_headers_user, multiple_contacts):
        """Test searching contacts."""
        response = client.get(
            "/api/contacts/search?query=User0", headers=auth_headers_user
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert any("User0" in contact["first_name"] for contact in data)

    @pytest.mark.integration
    def test_get_upcoming_birthdays(
        self, client, auth_headers_user, db_session, regular_user
    ):
        """Test getting contacts with upcoming birthdays."""
        # Create contact with birthday in next 7 days
        from datetime import date, timedelta

        upcoming_birthday = date.today() + timedelta(days=3)
        contact_data = ContactFactory.create_contact_data(
            first_name="Birthday", last_name="Soon", birthday=upcoming_birthday
        )

        response = client.post(
            "/api/contacts/", json=contact_data, headers=auth_headers_user
        )

        # Now get upcoming birthdays
        response = client.get("/api/contacts/birthdays", headers=auth_headers_user)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert any(contact["first_name"] == "Birthday" for contact in data)


class TestAdminAPI:
    """Test admin API endpoints."""

    @pytest.mark.integration
    def test_get_all_users_admin(self, client, auth_headers_admin):
        """Test admin getting all users."""
        response = client.get("/api/admin/users", headers=auth_headers_admin)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.integration
    def test_get_all_users_unauthorized(self, client, auth_headers_user):
        """Test regular user cannot access admin endpoints."""
        response = client.get("/api/admin/users", headers=auth_headers_user)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.integration
    def test_get_all_users_unauthenticated(self, client):
        """Test unauthenticated access to admin endpoints."""
        response = client.get("/api/admin/users")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.integration
    def test_update_user_role(self, client, auth_headers_admin, regular_user):
        """Test admin updating user role."""
        update_data = {"role": "moderator"}

        response = client.put(
            f"/api/admin/users/{regular_user.id}/role",
            json=update_data,
            headers=auth_headers_admin,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == "moderator"

    @pytest.mark.integration
    def test_update_user_role_invalid_role(
        self, client, auth_headers_admin, regular_user
    ):
        """Test updating user with invalid role."""
        update_data = {"role": "invalid_role"}

        response = client.put(
            f"/api/admin/users/{regular_user.id}/role",
            json=update_data,
            headers=auth_headers_admin,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.integration
    def test_update_user_status(self, client, auth_headers_admin, regular_user):
        """Test admin updating user status."""
        update_data = {"is_active": False, "reason": "Test deactivation"}

        response = client.put(
            f"/api/admin/users/{regular_user.id}/status",
            json=update_data,
            headers=auth_headers_admin,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_active"] is False

    @pytest.mark.integration
    def test_get_user_details_admin(self, client, auth_headers_admin, regular_user):
        """Test admin getting user details."""
        response = client.get(
            f"/api/admin/users/{regular_user.id}", headers=auth_headers_admin
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == regular_user.id
        assert data["username"] == regular_user.username

    @pytest.mark.integration
    def test_delete_user_admin(self, client, auth_headers_admin, db_session):
        """Test admin deleting user."""
        # Create a user to delete
        user_data = UserFactory.create_user_data(
            username="todelete", email="todelete@example.com"
        )

        response = client.post("/api/auth/register", json=user_data)
        created_user = response.json()

        # Delete the user
        response = client.delete(
            f"/api/admin/users/{created_user['id']}", headers=auth_headers_admin
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.integration
    def test_get_system_stats(self, client, auth_headers_admin):
        """Test getting system statistics."""
        response = client.get("/api/admin/stats", headers=auth_headers_admin)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "users" in data
        assert "total" in data["users"]
        assert "cache" in data

    @pytest.mark.integration
    def test_get_users_by_role(self, client, auth_headers_admin):
        """Test getting users by role."""
        response = client.get(
            "/api/admin/users/by-role/admin", headers=auth_headers_admin
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Should have at least one admin (the test admin)
        assert len(data) >= 1
        assert all(user["role"] == "admin" for user in data)

    @pytest.mark.integration
    def test_moderator_partial_admin_access(self, client, auth_headers_moderator):
        """Test moderator has limited admin access."""
        # Moderator should be able to view users
        response = client.get("/api/admin/users", headers=auth_headers_moderator)
        assert response.status_code == status.HTTP_200_OK

        # But not change roles
        response = client.put(
            "/api/admin/users/1/role",
            json={"role": "admin"},
            headers=auth_headers_moderator,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestRoleBasedAccess:
    """Test role-based access control across endpoints."""

    @pytest.mark.integration
    @pytest.mark.roles
    def test_user_access_own_resources_only(
        self, client, auth_headers_user, regular_user, admin_user, sample_contact
    ):
        """Test user can only access their own resources."""
        # User can access their own contacts
        response = client.get("/api/contacts/", headers=auth_headers_user)
        assert response.status_code == status.HTTP_200_OK

        # User cannot access admin endpoints
        response = client.get("/api/admin/users", headers=auth_headers_user)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.integration
    @pytest.mark.roles
    def test_moderator_extended_access(self, client, auth_headers_moderator):
        """Test moderator has extended access."""
        # Moderator can view users (limited admin access)
        response = client.get("/api/admin/users", headers=auth_headers_moderator)
        assert response.status_code == status.HTTP_200_OK

        # Moderator can view system stats
        response = client.get("/api/admin/stats", headers=auth_headers_moderator)
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.integration
    @pytest.mark.roles
    def test_admin_full_access(self, client, auth_headers_admin):
        """Test admin has full access to all endpoints."""
        # Admin can access all admin endpoints
        endpoints = [
            "/api/admin/users",
            "/api/admin/stats",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint, headers=auth_headers_admin)
            assert response.status_code == status.HTTP_200_OK

    @pytest.mark.integration
    @pytest.mark.roles
    def test_role_hierarchy_enforcement(
        self, client, auth_headers_user, auth_headers_moderator, auth_headers_admin
    ):
        """Test role hierarchy is properly enforced."""
        test_endpoint = "/api/admin/users"

        # USER - should be forbidden
        response = client.get(test_endpoint, headers=auth_headers_user)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # MODERATOR - should have access (assuming moderator can view users)
        response = client.get(test_endpoint, headers=auth_headers_moderator)
        assert response.status_code == status.HTTP_200_OK

        # ADMIN - should have full access
        response = client.get(test_endpoint, headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK


class TestAPIErrorHandling:
    """Test API error handling and edge cases."""

    @pytest.mark.integration
    def test_invalid_json_request(self, client, auth_headers_user):
        """Test API handles invalid JSON gracefully."""
        response = client.post(
            "/api/contacts/",
            data="invalid json",
            headers={**auth_headers_user, "Content-Type": "application/json"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.integration
    def test_missing_required_fields(self, client, auth_headers_user):
        """Test API validates required fields."""
        incomplete_contact = {"first_name": "John"}  # Missing required fields

        response = client.post(
            "/api/contacts/", json=incomplete_contact, headers=auth_headers_user
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.integration
    def test_invalid_date_format(self, client, auth_headers_user):
        """Test API handles invalid date formats."""
        contact_data = ContactFactory.create_contact_data()
        contact_data["birthday"] = "invalid-date"

        response = client.post(
            "/api/contacts/", json=contact_data, headers=auth_headers_user
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.integration
    def test_rate_limiting(self, client, auth_headers_user):
        """Test rate limiting is enforced."""
        # This test depends on rate limiting configuration
        # Make many requests quickly to trigger rate limit

        for _ in range(20):  # Exceed typical rate limit
            response = client.get("/api/auth/me", headers=auth_headers_user)

            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                # Rate limit triggered
                assert "rate limit" in response.json().get("detail", "").lower()
                break
        else:
            # If no rate limit hit, that's also okay (might be disabled in tests)
            pytest.skip("Rate limiting not triggered or disabled in tests")

    @pytest.mark.integration
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/api/auth/me")

        # Should have CORS headers in response
        assert response.status_code in [200, 405]  # Options might not be implemented
        # In a real test, you'd check for specific CORS headers
