"""
Тести для Pydantic schemas - валідація даних та серіалізація.
"""

import pytest
from datetime import date, datetime
from pydantic import ValidationError
from src.schemas import (
    UserRoleEnum,
    UserBase,
    UserCreate,
    UserResponse,
    ContactBase,
    ContactCreate,
    ContactResponse,
    Token,
    TokenData,
)


class TestUserSchemas:
    """Тести для схем користувачів."""

    def test_user_role_enum_values(self):
        """Тест значень UserRoleEnum."""
        assert UserRoleEnum.USER == "user"
        assert UserRoleEnum.MODERATOR == "moderator"
        assert UserRoleEnum.ADMIN == "admin"

    def test_user_base_valid(self):
        """Тест валідного UserBase."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
        }
        user = UserBase(**user_data)
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"

    def test_user_base_invalid_email(self):
        """Тест неправильного email в UserBase."""
        user_data = {
            "username": "testuser",
            "email": "invalid-email",
            "full_name": "Test User",
        }
        with pytest.raises(ValidationError):
            UserBase(**user_data)

    def test_user_create_valid(self):
        """Тест валідного UserCreate."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "full_name": "Test User",
        }
        user = UserCreate(**user_data)
        assert user.password == "testpass123"

    def test_user_create_missing_password(self):
        """Тест UserCreate без пароля."""
        user_data = {"username": "testuser", "email": "test@example.com"}
        with pytest.raises(ValidationError):
            UserCreate(**user_data)

    def test_user_response_valid(self):
        """Тест валідного UserResponse."""
        user_data = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "is_active": True,
            "role": UserRoleEnum.USER,
        }
        user = UserResponse(**user_data)
        assert user.id == 1
        assert user.role == UserRoleEnum.USER

    def test_user_response_default_values(self):
        """Тест значень за замовчуванням в UserResponse."""
        user_data = {"id": 1, "username": "testuser", "email": "test@example.com"}
        user = UserResponse(**user_data)
        assert user.is_active is True
        assert user.role is None

    def test_user_base_optional_fields(self):
        """Тест опціональних полів UserBase."""
        user_data = {"username": "testuser", "email": "test@example.com"}
        user = UserBase(**user_data)
        assert user.full_name is None
        assert user.avatar_url is None


class TestContactSchemas:
    """Тести для схем контактів."""

    def test_contact_base_valid(self):
        """Тест валідного ContactBase."""
        contact_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "birthday": date(1990, 1, 1),
        }
        contact = ContactBase(**contact_data)
        assert contact.first_name == "John"
        assert contact.last_name == "Doe"
        assert contact.birthday == date(1990, 1, 1)

    def test_contact_base_invalid_email(self):
        """Тест неправильного email в ContactBase."""
        contact_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "invalid-email",
            "phone": "+1234567890",
            "birthday": date(1990, 1, 1),
        }
        with pytest.raises(ValidationError):
            ContactBase(**contact_data)

    def test_contact_create_valid(self):
        """Тест валідного ContactCreate."""
        contact_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "birthday": date(1990, 1, 1),
            "additional_info": "Test contact",
        }
        contact = ContactCreate(**contact_data)
        assert contact.additional_info == "Test contact"

    def test_contact_response_valid(self):
        """Тест валідного ContactResponse."""
        contact_data = {
            "id": 1,
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "birthday": date(1990, 1, 1),
            "user_id": 1,
        }
        contact = ContactResponse(**contact_data)
        assert contact.id == 1
        assert contact.user_id == 1

    def test_contact_optional_additional_info(self):
        """Тест опціонального поля additional_info."""
        contact_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "birthday": date(1990, 1, 1),
        }
        contact = ContactBase(**contact_data)
        assert contact.additional_info is None


class TestAuthSchemas:
    """Тести для схем аутентифікації."""

    def test_token_valid(self):
        """Тест валідного Token."""
        token_data = {"access_token": "test.jwt.token", "token_type": "bearer"}
        token = Token(**token_data)
        assert token.access_token == "test.jwt.token"
        assert token.token_type == "bearer"

    def test_token_data_valid(self):
        """Тест валідного TokenData."""
        token_data = {"username": "testuser"}
        token = TokenData(**token_data)
        assert token.username == "testuser"

    def test_token_data_none_username(self):
        """Тест TokenData з None username."""
        token_data = {}
        token = TokenData(**token_data)
        assert token.username is None


class TestSchemaSerialization:
    """Тести серіалізації схем."""

    def test_user_response_dict(self):
        """Тест серіалізації UserResponse в dict."""
        user_data = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "is_active": True,
            "role": UserRoleEnum.USER,
        }
        user = UserResponse(**user_data)
        user_dict = user.model_dump()

        assert user_dict["id"] == 1
        assert user_dict["username"] == "testuser"
        assert user_dict["role"] == "user"

    def test_contact_response_dict(self):
        """Тест серіалізації ContactResponse в dict."""
        contact_data = {
            "id": 1,
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "birthday": date(1990, 1, 1),
            "user_id": 1,
        }
        contact = ContactResponse(**contact_data)
        contact_dict = contact.model_dump()

        assert contact_dict["id"] == 1
        assert contact_dict["first_name"] == "John"
        assert contact_dict["birthday"] == date(1990, 1, 1)

    def test_schema_json_serialization(self):
        """Тест JSON серіалізації схем."""
        user_data = {"id": 1, "username": "testuser", "email": "test@example.com"}
        user = UserResponse(**user_data)
        json_str = user.model_dump_json()

        assert '"username":"testuser"' in json_str
        assert '"id":1' in json_str


class TestSchemaValidation:
    """Тести валідації схем."""

    def test_empty_username_validation(self):
        """Тест валідації порожнього username."""
        user_data = {"username": "", "email": "test@example.com"}
        with pytest.raises(ValidationError):
            UserBase(**user_data)

    def test_missing_required_fields(self):
        """Тест відсутності обов'язкових полів."""
        user_data = {"email": "test@example.com"}
        with pytest.raises(ValidationError):
            UserBase(**user_data)

    def test_contact_missing_required_fields(self):
        """Тест відсутності обов'язкових полів у контакті."""
        contact_data = {"first_name": "John"}
        with pytest.raises(ValidationError):
            ContactBase(**contact_data)

    def test_invalid_date_format(self):
        """Тест неправильного формату дати."""
        contact_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "birthday": "invalid-date",
        }
        with pytest.raises(ValidationError):
            ContactBase(**contact_data)
