"""
Unit tests for database models.

Tests for User and Contact models including role validation,
relationships, and model constraints.
"""

import pytest
from datetime import date, datetime
from sqlalchemy.exc import IntegrityError

from src.database.models import User, Contact, UserRole


class TestUserModel:
    """Test User model functionality."""

    @pytest.mark.unit
    def test_create_user_with_default_role(self, db_session):
        """Test creating user with default USER role."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password_123",
            full_name="Test User",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.is_verified is False

    @pytest.mark.unit
    def test_create_user_with_admin_role(self, db_session):
        """Test creating user with ADMIN role."""
        user = User(
            username="admin",
            email="admin@example.com",
            hashed_password="hashed_password_123",
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.role == UserRole.ADMIN
        assert user.is_verified is True

    @pytest.mark.unit
    def test_create_user_with_moderator_role(self, db_session):
        """Test creating user with MODERATOR role."""
        user = User(
            username="moderator",
            email="moderator@example.com",
            hashed_password="hashed_password_123",
            full_name="Moderator User",
            role=UserRole.MODERATOR,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.role == UserRole.MODERATOR

    @pytest.mark.unit
    def test_user_unique_username(self, db_session):
        """Test that username must be unique."""
        user1 = User(
            username="duplicate",
            email="user1@example.com",
            hashed_password="hashed_password_123",
        )
        user2 = User(
            username="duplicate",
            email="user2@example.com",
            hashed_password="hashed_password_123",
        )

        db_session.add(user1)
        db_session.commit()

        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    @pytest.mark.unit
    def test_user_unique_email(self, db_session):
        """Test that email must be unique."""
        user1 = User(
            username="user1",
            email="duplicate@example.com",
            hashed_password="hashed_password_123",
        )
        user2 = User(
            username="user2",
            email="duplicate@example.com",
            hashed_password="hashed_password_123",
        )

        db_session.add(user1)
        db_session.commit()

        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    @pytest.mark.unit
    def test_user_str_representation(self, db_session):
        """Test User __repr__ method."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password_123",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        expected = (
            f"<User(id={user.id}, username='testuser', email='test@example.com')>"
        )
        assert repr(user) == expected

    @pytest.mark.unit
    def test_user_role_enum_values(self):
        """Test UserRole enum values."""
        assert UserRole.USER.value == "user"
        assert UserRole.MODERATOR.value == "moderator"
        assert UserRole.ADMIN.value == "admin"

    @pytest.mark.unit
    def test_user_optional_fields(self, db_session):
        """Test user creation with optional fields."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password_123",
            full_name="Test User",
            avatar_url="http://example.com/avatar.jpg",
            verification_token="verification_token_123",
            reset_token="reset_token_123",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.full_name == "Test User"
        assert user.avatar_url == "http://example.com/avatar.jpg"
        assert user.verification_token == "verification_token_123"
        assert user.reset_token == "reset_token_123"

    @pytest.mark.unit
    def test_user_inactive_status(self, db_session):
        """Test creating inactive user."""
        user = User(
            username="inactive",
            email="inactive@example.com",
            hashed_password="hashed_password_123",
            is_active=False,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.is_active is False


class TestContactModel:
    """Test Contact model functionality."""

    @pytest.mark.unit
    def test_create_contact(self, db_session, regular_user):
        """Test creating a contact."""
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

        assert contact.id is not None
        assert contact.first_name == "John"
        assert contact.last_name == "Doe"
        assert contact.email == "john.doe@example.com"
        assert contact.phone == "+1234567890"
        assert contact.birthday == date(1990, 1, 15)
        assert contact.additional_info == "Test contact"
        assert contact.user_id == regular_user.id

    @pytest.mark.unit
    def test_contact_user_relationship(self, db_session, regular_user):
        """Test contact-user relationship."""
        contact = Contact(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            phone="+1234567891",
            birthday=date(1985, 6, 20),
            user_id=regular_user.id,
        )
        db_session.add(contact)
        db_session.commit()
        db_session.refresh(contact)

        # Test relationship from contact to user
        assert contact.owner.id == regular_user.id
        assert contact.owner.username == regular_user.username

        # Test relationship from user to contact
        assert len(regular_user.contacts) > 0
        assert contact in regular_user.contacts

    @pytest.mark.unit
    def test_contact_str_representation(self, db_session, regular_user):
        """Test Contact __repr__ method."""
        contact = Contact(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+1234567890",
            birthday=date(1990, 1, 15),
            user_id=regular_user.id,
        )
        db_session.add(contact)
        db_session.commit()
        db_session.refresh(contact)

        expected = f"<Contact(id={contact.id}, first_name='John', last_name='Doe', email='john.doe@example.com')>"
        assert repr(contact) == expected

    @pytest.mark.unit
    def test_contact_without_additional_info(self, db_session, regular_user):
        """Test creating contact without additional info."""
        contact = Contact(
            first_name="Bob",
            last_name="Wilson",
            email="bob.wilson@example.com",
            phone="+1234567892",
            birthday=date(1992, 3, 10),
            user_id=regular_user.id,
        )
        db_session.add(contact)
        db_session.commit()
        db_session.refresh(contact)

        assert contact.additional_info is None

    @pytest.mark.unit
    def test_multiple_contacts_same_email_different_users(
        self, db_session, regular_user, admin_user
    ):
        """Test that multiple users can have contacts with same email."""
        contact1 = Contact(
            first_name="John",
            last_name="Doe",
            email="same@example.com",
            phone="+1111111111",
            birthday=date(1990, 1, 1),
            user_id=regular_user.id,
        )

        contact2 = Contact(
            first_name="Jane",
            last_name="Doe",
            email="same@example.com",
            phone="+2222222222",
            birthday=date(1991, 2, 2),
            user_id=admin_user.id,
        )

        db_session.add_all([contact1, contact2])
        db_session.commit()

        # Should not raise any constraint errors
        assert contact1.email == contact2.email
        assert contact1.user_id != contact2.user_id

    @pytest.mark.unit
    def test_contact_foreign_key_constraint(self, db_session):
        """Test that contact requires valid user_id."""
        contact = Contact(
            first_name="Invalid",
            last_name="User",
            email="invalid@example.com",
            phone="+1234567893",
            birthday=date(1990, 1, 1),
            user_id=999999,  # Non-existent user ID
        )
        db_session.add(contact)

        with pytest.raises(IntegrityError):
            db_session.commit()


class TestModelRelationships:
    """Test model relationships and cascading operations."""

    @pytest.mark.unit
    def test_user_contacts_relationship(self, db_session, regular_user):
        """Test user can have multiple contacts."""
        contacts = []
        for i in range(3):
            contact = Contact(
                first_name=f"Contact{i}",
                last_name="Test",
                email=f"contact{i}@example.com",
                phone=f"+123456789{i}",
                birthday=date(1990 + i, 1, 1),
                user_id=regular_user.id,
            )
            contacts.append(contact)
            db_session.add(contact)

        db_session.commit()

        # Refresh user to load relationships
        db_session.refresh(regular_user)

        assert len(regular_user.contacts) == 3
        for contact in contacts:
            assert contact in regular_user.contacts

    @pytest.mark.unit
    def test_user_deletion_affects_contacts(self, db_session):
        """Test what happens to contacts when user is deleted."""
        # Create user
        user = User(
            username="todelete",
            email="todelete@example.com",
            hashed_password="hashed_password_123",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Create contact
        contact = Contact(
            first_name="Will",
            last_name="BeOrphaned",
            email="orphaned@example.com",
            phone="+1234567894",
            birthday=date(1990, 1, 1),
            user_id=user.id,
        )
        db_session.add(contact)
        db_session.commit()

        # Delete user
        db_session.delete(user)

        # This should raise an IntegrityError due to foreign key constraint
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestModelValidation:
    """Test model field validation and constraints."""

    @pytest.mark.unit
    def test_user_required_fields(self, db_session):
        """Test that required user fields must be provided."""
        # Missing username
        with pytest.raises(Exception):
            user = User(email="test@example.com", hashed_password="hashed_password_123")
            db_session.add(user)
            db_session.commit()

    @pytest.mark.unit
    def test_contact_required_fields(self, db_session, regular_user):
        """Test that required contact fields must be provided."""
        # Missing first_name
        with pytest.raises(Exception):
            contact = Contact(
                last_name="Doe",
                email="john.doe@example.com",
                phone="+1234567890",
                birthday=date(1990, 1, 15),
                user_id=regular_user.id,
            )
            db_session.add(contact)
            db_session.commit()

    @pytest.mark.unit
    def test_user_role_default_value(self, db_session):
        """Test that user role defaults to USER."""
        user = User(
            username="defaultrole",
            email="defaultrole@example.com",
            hashed_password="hashed_password_123",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.role == UserRole.USER

    @pytest.mark.unit
    def test_user_boolean_defaults(self, db_session):
        """Test boolean field defaults."""
        user = User(
            username="booltest",
            email="booltest@example.com",
            hashed_password="hashed_password_123",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.is_active is True
        assert user.is_verified is False
