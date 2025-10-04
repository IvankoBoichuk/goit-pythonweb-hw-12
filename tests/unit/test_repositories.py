"""
Unit tests for repository layer.

Tests for UserRepository and ContactRepository with mocked database operations.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import date, datetime
from sqlalchemy.exc import IntegrityError

from src.repository.users import UserRepository
from src.repository.contacts import ContactRepository
from src.database.models import User, Contact, UserRole


class TestUserRepository:
    """Test UserRepository functionality."""

    @pytest.mark.unit
    def test_get_user_by_username(self, db_session):
        """Test getting user by username."""
        # Setup
        repo = UserRepository(db_session)
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_pass",
            role=UserRole.USER,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Test
        result = repo.get_user_by_username("testuser")

        # Assert
        assert result is not None
        assert result.username == "testuser"
        assert result.email == "test@example.com"

    @pytest.mark.unit
    def test_get_user_by_username_not_found(self, db_session):
        """Test getting non-existent user by username."""
        repo = UserRepository(db_session)

        result = repo.get_user_by_username("nonexistent")

        assert result is None

    @pytest.mark.unit
    def test_get_user_by_email(self, db_session):
        """Test getting user by email."""
        repo = UserRepository(db_session)
        user = User(
            username="testuser", email="test@example.com", hashed_password="hashed_pass"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        result = repo.get_user_by_email("test@example.com")

        assert result is not None
        assert result.email == "test@example.com"

    @pytest.mark.unit
    def test_create_user(self, db_session):
        """Test creating a new user."""
        repo = UserRepository(db_session)
        user_data = {
            "username": "newuser",
            "email": "new@example.com",
            "hashed_password": "hashed_pass",
            "full_name": "New User",
        }

        result = repo.create_user(**user_data)

        assert result.username == "newuser"
        assert result.email == "new@example.com"
        assert result.full_name == "New User"
        assert result.role == UserRole.USER
        assert result.id is not None

    @pytest.mark.unit
    def test_update_user_role(self, db_session, regular_user):
        """Test updating user role."""
        repo = UserRepository(db_session)

        result = repo.update_user_role(regular_user.id, UserRole.MODERATOR)

        assert result is not None
        assert result.role == UserRole.MODERATOR

        # Verify in database
        updated_user = repo.get_user_by_id(regular_user.id)
        assert updated_user.role == UserRole.MODERATOR

    @pytest.mark.unit
    def test_update_user_role_invalid_user(self, db_session):
        """Test updating role for non-existent user."""
        repo = UserRepository(db_session)

        result = repo.update_user_role(999999, UserRole.ADMIN)

        assert result is None

    @pytest.mark.unit
    def test_get_users_by_role(self, db_session):
        """Test getting users by role."""
        repo = UserRepository(db_session)

        # Create users with different roles
        admin_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password="pass",
            role=UserRole.ADMIN,
        )
        moderator_user = User(
            username="mod",
            email="mod@example.com",
            hashed_password="pass",
            role=UserRole.MODERATOR,
        )
        regular_user = User(
            username="user",
            email="user@example.com",
            hashed_password="pass",
            role=UserRole.USER,
        )

        db_session.add_all([admin_user, moderator_user, regular_user])
        db_session.commit()

        # Test getting admins
        admins = repo.get_users_by_role(UserRole.ADMIN)
        assert len(admins) == 1
        assert admins[0].role == UserRole.ADMIN

        # Test getting moderators
        moderators = repo.get_users_by_role(UserRole.MODERATOR)
        assert len(moderators) == 1
        assert moderators[0].role == UserRole.MODERATOR

    @pytest.mark.unit
    def test_get_all_users(self, db_session):
        """Test getting all users with pagination."""
        repo = UserRepository(db_session)

        # Create multiple users
        for i in range(15):
            user = User(
                username=f"user{i}",
                email=f"user{i}@example.com",
                hashed_password="pass",
            )
            db_session.add(user)
        db_session.commit()

        # Test with pagination
        users = repo.get_all_users(skip=0, limit=10)
        assert len(users) == 10

        # Test second page
        users_page2 = repo.get_all_users(skip=10, limit=10)
        assert len(users_page2) == 5

    @pytest.mark.unit
    def test_get_users_count(self, db_session):
        """Test getting total users count."""
        repo = UserRepository(db_session)

        # Add some users
        for i in range(5):
            user = User(
                username=f"count_user{i}",
                email=f"count{i}@example.com",
                hashed_password="pass",
            )
            db_session.add(user)
        db_session.commit()

        count = repo.get_users_count()
        assert count == 5

    @pytest.mark.unit
    def test_update_user_status(self, db_session, regular_user):
        """Test updating user active status."""
        repo = UserRepository(db_session)

        # Deactivate user
        result = repo.update_user_status(regular_user.id, False)
        assert result is not None
        assert result.is_active is False

        # Activate user
        result = repo.update_user_status(regular_user.id, True)
        assert result is not None
        assert result.is_active is True

    @pytest.mark.unit
    def test_search_users(self, db_session):
        """Test searching users by username or email."""
        repo = UserRepository(db_session)

        users_data = [
            {"username": "john_doe", "email": "john@example.com"},
            {"username": "jane_smith", "email": "jane@test.com"},
            {"username": "bob_wilson", "email": "bob@example.org"},
        ]

        for data in users_data:
            user = User(hashed_password="pass", **data)
            db_session.add(user)
        db_session.commit()

        # Search by username
        results = repo.search_users("john")
        assert len(results) == 1
        assert results[0].username == "john_doe"

        # Search by email domain
        results = repo.search_users("example.com")
        assert len(results) == 1
        assert results[0].email == "john@example.com"

    @pytest.mark.unit
    def test_delete_user(self, db_session, regular_user):
        """Test deleting a user."""
        repo = UserRepository(db_session)
        user_id = regular_user.id

        success = repo.delete_user(user_id)
        assert success is True

        # Verify user is deleted
        deleted_user = repo.get_user_by_id(user_id)
        assert deleted_user is None

    @pytest.mark.unit
    def test_update_verification_status(self, db_session, regular_user):
        """Test updating user verification status."""
        repo = UserRepository(db_session)

        result = repo.update_verification_status(regular_user.id, True)
        assert result is not None
        assert result.is_verified is True


class TestContactRepository:
    """Test ContactRepository functionality."""

    @pytest.mark.unit
    def test_get_contacts_for_user(self, db_session, regular_user):
        """Test getting contacts for a user."""
        repo = ContactRepository(db_session)

        # Create contacts for user
        for i in range(3):
            contact = Contact(
                first_name=f"Contact{i}",
                last_name="Test",
                email=f"contact{i}@example.com",
                phone=f"+123456789{i}",
                birthday=date(1990 + i, 1, 1),
                user_id=regular_user.id,
            )
            db_session.add(contact)
        db_session.commit()

        contacts = repo.get_contacts(regular_user.id, skip=0, limit=10)
        assert len(contacts) == 3

    @pytest.mark.unit
    def test_get_contacts_pagination(self, db_session, regular_user):
        """Test contacts pagination."""
        repo = ContactRepository(db_session)

        # Create 15 contacts
        for i in range(15):
            contact = Contact(
                first_name=f"Contact{i}",
                last_name="Test",
                email=f"contact{i}@example.com",
                phone=f"+123456789{i}",
                birthday=date(1990, 1, 1),
                user_id=regular_user.id,
            )
            db_session.add(contact)
        db_session.commit()

        # Test first page
        page1 = repo.get_contacts(regular_user.id, skip=0, limit=10)
        assert len(page1) == 10

        # Test second page
        page2 = repo.get_contacts(regular_user.id, skip=10, limit=10)
        assert len(page2) == 5

    @pytest.mark.unit
    def test_get_contact_by_id(self, db_session, regular_user, sample_contact):
        """Test getting contact by ID."""
        repo = ContactRepository(db_session)

        result = repo.get_contact_by_id(sample_contact.id, regular_user.id)

        assert result is not None
        assert result.id == sample_contact.id
        assert result.first_name == sample_contact.first_name

    @pytest.mark.unit
    def test_get_contact_by_id_wrong_user(self, db_session, admin_user, sample_contact):
        """Test getting contact by ID with wrong user."""
        repo = ContactRepository(db_session)

        # Try to get contact with different user
        result = repo.get_contact_by_id(sample_contact.id, admin_user.id)

        assert result is None

    @pytest.mark.unit
    def test_create_contact(self, db_session, regular_user):
        """Test creating a new contact."""
        repo = ContactRepository(db_session)

        contact_data = {
            "first_name": "New",
            "last_name": "Contact",
            "email": "new@example.com",
            "phone": "+1111111111",
            "birthday": date(1995, 5, 15),
            "additional_info": "New contact info",
        }

        result = repo.create_contact(regular_user.id, **contact_data)

        assert result.first_name == "New"
        assert result.last_name == "Contact"
        assert result.user_id == regular_user.id
        assert result.id is not None

    @pytest.mark.unit
    def test_update_contact(self, db_session, regular_user, sample_contact):
        """Test updating a contact."""
        repo = ContactRepository(db_session)

        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "phone": "+9999999999",
        }

        result = repo.update_contact(sample_contact.id, regular_user.id, **update_data)

        assert result is not None
        assert result.first_name == "Updated"
        assert result.last_name == "Name"
        assert result.phone == "+9999999999"
        # Other fields should remain unchanged
        assert result.email == sample_contact.email

    @pytest.mark.unit
    def test_update_contact_wrong_user(self, db_session, admin_user, sample_contact):
        """Test updating contact with wrong user."""
        repo = ContactRepository(db_session)

        result = repo.update_contact(
            sample_contact.id, admin_user.id, first_name="Should Not Update"
        )

        assert result is None

    @pytest.mark.unit
    def test_delete_contact(self, db_session, regular_user, sample_contact):
        """Test deleting a contact."""
        repo = ContactRepository(db_session)
        contact_id = sample_contact.id

        success = repo.delete_contact(contact_id, regular_user.id)
        assert success is True

        # Verify contact is deleted
        deleted_contact = repo.get_contact_by_id(contact_id, regular_user.id)
        assert deleted_contact is None

    @pytest.mark.unit
    def test_delete_contact_wrong_user(self, db_session, admin_user, sample_contact):
        """Test deleting contact with wrong user."""
        repo = ContactRepository(db_session)

        success = repo.delete_contact(sample_contact.id, admin_user.id)
        assert success is False

        # Verify contact still exists
        existing_contact = repo.get_contact_by_id(
            sample_contact.id, sample_contact.user_id
        )
        assert existing_contact is not None

    @pytest.mark.unit
    def test_search_contacts(self, db_session, regular_user):
        """Test searching contacts by name or email."""
        repo = ContactRepository(db_session)

        contacts_data = [
            {"first_name": "John", "last_name": "Doe", "email": "john@example.com"},
            {"first_name": "Jane", "last_name": "Smith", "email": "jane@test.com"},
            {"first_name": "Bob", "last_name": "Johnson", "email": "bob@example.org"},
        ]

        for data in contacts_data:
            contact = Contact(
                phone="+1234567890",
                birthday=date(1990, 1, 1),
                user_id=regular_user.id,
                **data,
            )
            db_session.add(contact)
        db_session.commit()

        # Search by first name
        results = repo.search_contacts(regular_user.id, "John")
        assert len(results) == 1
        assert results[0].first_name == "John"

        # Search by last name
        results = repo.search_contacts(regular_user.id, "Smith")
        assert len(results) == 1
        assert results[0].last_name == "Smith"

        # Search by email
        results = repo.search_contacts(regular_user.id, "example.com")
        assert len(results) == 1

    @pytest.mark.unit
    def test_get_contacts_by_birthday_range(self, db_session, regular_user):
        """Test getting contacts by birthday range."""
        repo = ContactRepository(db_session)

        # Create contacts with different birthdays
        birthdays = [
            date(1990, 1, 15),
            date(1992, 6, 20),
            date(1995, 12, 31),
            date(1988, 3, 10),
        ]

        for i, birthday in enumerate(birthdays):
            contact = Contact(
                first_name=f"Contact{i}",
                last_name="Test",
                email=f"contact{i}@example.com",
                phone=f"+123456789{i}",
                birthday=birthday,
                user_id=regular_user.id,
            )
            db_session.add(contact)
        db_session.commit()

        # Search for contacts born between 1990 and 1993
        results = repo.get_contacts_by_birthday_range(
            regular_user.id, date(1990, 1, 1), date(1993, 12, 31)
        )

        assert len(results) == 2
        birth_years = [contact.birthday.year for contact in results]
        assert 1990 in birth_years
        assert 1992 in birth_years


class TestRepositoryErrorHandling:
    """Test repository error handling and edge cases."""

    @pytest.mark.unit
    def test_user_repository_database_error(self, db_session):
        """Test UserRepository handles database errors."""
        repo = UserRepository(db_session)

        # Create user with duplicate username (should fail)
        user1 = User(
            username="duplicate", email="user1@example.com", hashed_password="pass"
        )
        db_session.add(user1)
        db_session.commit()

        # Try to create another user with same username
        with pytest.raises(Exception):
            repo.create_user(
                username="duplicate", email="user2@example.com", hashed_password="pass"
            )

    @pytest.mark.unit
    def test_contact_repository_database_error(self, db_session):
        """Test ContactRepository handles database errors."""
        repo = ContactRepository(db_session)

        # Try to create contact with invalid user_id
        with pytest.raises(Exception):
            repo.create_contact(
                user_id=999999,  # Non-existent user
                first_name="Test",
                last_name="Contact",
                email="test@example.com",
                phone="+1234567890",
                birthday=date(1990, 1, 1),
            )

    @pytest.mark.unit
    def test_repository_with_closed_session(self, db_session):
        """Test repository behavior with closed session."""
        repo = UserRepository(db_session)

        # Close the session
        db_session.close()

        # Operations should fail gracefully
        with pytest.raises(Exception):
            repo.get_user_by_username("test")


class TestRepositoryMocking:
    """Test repository with mocked dependencies."""

    @pytest.mark.unit
    def test_user_repository_with_mock_db(self):
        """Test UserRepository with mocked database session."""
        mock_session = Mock()
        mock_query = Mock()
        mock_user = Mock()
        mock_user.username = "testuser"

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_user

        repo = UserRepository(mock_session)
        result = repo.get_user_by_username("testuser")

        assert result.username == "testuser"
        mock_session.query.assert_called_once()

    @pytest.mark.unit
    def test_contact_repository_with_mock_db(self):
        """Test ContactRepository with mocked database session."""
        mock_session = Mock()
        mock_query = Mock()
        mock_contacts = [Mock(), Mock(), Mock()]

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_contacts

        repo = ContactRepository(mock_session)
        result = repo.get_contacts(user_id=1, skip=0, limit=10)

        assert len(result) == 3
        mock_session.query.assert_called_once()
        mock_query.filter.assert_called_once()
        mock_query.offset.assert_called_once_with(0)
        mock_query.limit.assert_called_once_with(10)
