"""
Test configuration and fixtures for the FastAPI Contacts API.

This module provides pytest fixtures for database setup, test client,
and common test utilities for both unit and integration tests.
"""

import asyncio
import os
import pytest
import pytest_asyncio
from datetime import datetime, date
from unittest.mock import Mock, AsyncMock
from typing import Generator, AsyncGenerator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import redis

# Import application modules
from main import app
from src.database.db import get_db, Base
from src.database.models import User, Contact, UserRole
from src.services.cache import CacheService
from src.conf.config import settings


# Test database configuration
TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine with in-memory SQLite
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    """Create a test client for FastAPI application."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing cache functionality."""
    mock_client = Mock()
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.delete.return_value = 1
    mock_client.exists.return_value = 0
    mock_client.ping.return_value = True
    return mock_client


@pytest.fixture
def cache_service(mock_redis):
    """Create CacheService with mocked Redis."""
    service = CacheService()
    service.redis_client = mock_redis
    return service


# User fixtures for different roles
@pytest.fixture
def admin_user(db_session):
    """Create an admin user for testing."""
    user = User(
        username="admin_test",
        email="admin@test.com",
        hashed_password="$pbkdf2-sha256$29000$test",
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def moderator_user(db_session):
    """Create a moderator user for testing."""
    user = User(
        username="moderator_test",
        email="moderator@test.com",
        hashed_password="$pbkdf2-sha256$29000$test",
        full_name="Moderator User",
        role=UserRole.MODERATOR,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def regular_user(db_session):
    """Create a regular user for testing."""
    user = User(
        username="user_test",
        email="user@test.com",
        hashed_password="$pbkdf2-sha256$29000$test",
        full_name="Regular User",
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def inactive_user(db_session):
    """Create an inactive user for testing."""
    user = User(
        username="inactive_test",
        email="inactive@test.com",
        hashed_password="$pbkdf2-sha256$29000$test",
        full_name="Inactive User",
        role=UserRole.USER,
        is_active=False,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_contact(db_session, regular_user):
    """Create a sample contact for testing."""
    contact = Contact(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="+1234567890",
        birthday=date(1990, 1, 15),
        additional_info="Test contact",
        user_id=regular_user.id,
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)
    return contact


@pytest.fixture
def multiple_contacts(db_session, regular_user):
    """Create multiple contacts for pagination testing."""
    contacts = []
    for i in range(15):
        contact = Contact(
            first_name=f"User{i}",
            last_name=f"Test{i}",
            email=f"user{i}@test.com",
            phone=f"+123456789{i}",
            birthday=date(1990 + i % 10, 1, 1),
            additional_info=f"Test contact {i}",
            user_id=regular_user.id,
        )
        db_session.add(contact)
        contacts.append(contact)

    db_session.commit()
    for contact in contacts:
        db_session.refresh(contact)
    return contacts


# Authentication helpers
@pytest.fixture
def auth_headers_admin(client, admin_user):
    """Get authentication headers for admin user."""
    from src.services.auth import AuthService

    token_data = {"sub": admin_user.username, "role": admin_user.role.value}
    token = AuthService.create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_moderator(client, moderator_user):
    """Get authentication headers for moderator user."""
    from src.services.auth import AuthService

    token_data = {"sub": moderator_user.username, "role": moderator_user.role.value}
    token = AuthService.create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_user(client, regular_user):
    """Get authentication headers for regular user."""
    from src.services.auth import AuthService

    token_data = {"sub": regular_user.username, "role": regular_user.role.value}
    token = AuthService.create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}


# Mock services
@pytest.fixture
def mock_email_service():
    """Mock email service for testing."""
    mock = Mock()
    mock.send_verification_email = Mock()
    mock.send_password_reset_email = Mock()
    return mock


@pytest.fixture
def mock_cloudinary_service():
    """Mock Cloudinary service for testing."""
    mock = Mock()
    mock.upload_image = Mock(return_value="http://test.cloudinary.com/test_image.jpg")
    mock.delete_image = Mock(return_value=True)
    return mock


# Test data factories
class UserFactory:
    """Factory for creating test users."""

    @staticmethod
    def create_user_data(
        username: str = "testuser",
        email: str = "test@example.com",
        password: str = "testpassword123",
        full_name: str = "Test User",
        role: UserRole = UserRole.USER,
    ) -> dict:
        """Create user data dictionary."""
        return {
            "username": username,
            "email": email,
            "password": password,
            "full_name": full_name,
            "role": role,
        }


class ContactFactory:
    """Factory for creating test contacts."""

    @staticmethod
    def create_contact_data(
        first_name: str = "John",
        last_name: str = "Doe",
        email: str = "john.doe@example.com",
        phone: str = "+1234567890",
        birthday: date = None,
        additional_info: str = "Test contact",
    ) -> dict:
        """Create contact data dictionary."""
        if birthday is None:
            birthday = date(1990, 1, 15)

        return {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "birthday": birthday.isoformat(),
            "additional_info": additional_info,
        }


# Pytest configuration
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    os.environ["TESTING"] = "1"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["REDIS_URL"] = "redis://localhost:6380"
    yield
    if "TESTING" in os.environ:
        del os.environ["TESTING"]


# Utility functions
def assert_user_response(response_data: dict, expected_user: User):
    """Assert user response data matches expected user."""
    assert response_data["id"] == expected_user.id
    assert response_data["username"] == expected_user.username
    assert response_data["email"] == expected_user.email
    assert response_data["full_name"] == expected_user.full_name
    assert response_data["is_active"] == expected_user.is_active
    assert response_data["role"] == expected_user.role.value


def assert_contact_response(response_data: dict, expected_contact: Contact):
    """Assert contact response data matches expected contact."""
    assert response_data["id"] == expected_contact.id
    assert response_data["first_name"] == expected_contact.first_name
    assert response_data["last_name"] == expected_contact.last_name
    assert response_data["email"] == expected_contact.email
    assert response_data["phone"] == expected_contact.phone
    assert response_data["birthday"] == expected_contact.birthday.isoformat()
    assert response_data["additional_info"] == expected_contact.additional_info
