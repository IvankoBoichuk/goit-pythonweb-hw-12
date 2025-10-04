"""
Додаткові тести для покращення покриття коду.
Ці тести не потребують складних фікстур і працюють безпосередньо з кодом.
"""

import pytest
from datetime import date
from src.database.models import UserRole, User, Contact


class TestSimpleModels:
    """Прості тести моделей без бази даних."""

    def test_user_role_enum_values(self):
        """Тест значень enum UserRole."""
        assert UserRole.USER.value == "user"
        assert UserRole.MODERATOR.value == "moderator"
        assert UserRole.ADMIN.value == "admin"

    def test_user_repr(self):
        """Тест __repr__ методу User моделі."""
        user = User()
        user.id = 1
        user.username = "testuser"
        user.email = "test@example.com"

        repr_str = repr(user)
        assert "User" in repr_str
        assert "testuser" in repr_str
        assert "test@example.com" in repr_str

    def test_contact_repr(self):
        """Тест __repr__ методу Contact моделі."""
        contact = Contact()
        contact.id = 1
        contact.first_name = "John"
        contact.last_name = "Doe"
        contact.email = "john@example.com"

        repr_str = repr(contact)
        assert "Contact" in repr_str
        assert "John" in repr_str
        assert "Doe" in repr_str
        assert "john@example.com" in repr_str

    def test_user_role_enum_iteration(self):
        """Тест ітерації по UserRole enum."""
        roles = list(UserRole)
        assert len(roles) == 3
        assert UserRole.USER in roles
        assert UserRole.MODERATOR in roles
        assert UserRole.ADMIN in roles

    def test_user_model_attributes(self):
        """Тест що User модель має всі необхідні атрибути."""
        user = User()

        # Перевіримо що атрибути існують
        assert hasattr(user, "id")
        assert hasattr(user, "username")
        assert hasattr(user, "email")
        assert hasattr(user, "hashed_password")
        assert hasattr(user, "full_name")
        assert hasattr(user, "is_active")
        assert hasattr(user, "is_verified")
        assert hasattr(user, "verification_token")
        assert hasattr(user, "avatar_url")
        assert hasattr(user, "role")

    def test_contact_model_attributes(self):
        """Тест що Contact модель має всі необхідні атрибути."""
        contact = Contact()

        # Перевіримо що атрибути існують
        assert hasattr(contact, "id")
        assert hasattr(contact, "first_name")
        assert hasattr(contact, "last_name")
        assert hasattr(contact, "email")
        assert hasattr(contact, "phone")
        assert hasattr(contact, "birthday")
        assert hasattr(contact, "additional_info")
        assert hasattr(contact, "user_id")

    def test_user_role_comparison(self):
        """Тест порівняння ролей."""
        user_role = UserRole.USER
        moderator_role = UserRole.MODERATOR
        admin_role = UserRole.ADMIN

        assert user_role == UserRole.USER
        assert moderator_role != UserRole.USER
        assert admin_role != UserRole.MODERATOR

    def test_model_table_names(self):
        """Тест імен таблиць моделей."""
        assert User.__tablename__ == "users"
        assert Contact.__tablename__ == "contacts"
