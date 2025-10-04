from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from src.database.models import User
from src.schemas import UserCreate
from src.services.auth import AuthService


class UserRepository:
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get user by username."""
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create_user(db: Session, user: UserCreate) -> User:
        """Create a new user."""
        hashed_password = AuthService.get_password_hash(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            hashed_password=hashed_password,
            is_active=True,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password."""
        user = UserRepository.get_user_by_username(db, username)
        if not user:
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    def update_avatar(db: Session, user_id: int, avatar_url: str) -> Optional[User]:
        """Update user avatar URL."""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.avatar_url = avatar_url
            db.commit()
            db.refresh(user)
        return user

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def update_user(db: Session, user_id: int, **kwargs) -> Optional[User]:
        """Update user with provided fields."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """Delete user by ID."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        db.delete(user)
        db.commit()
        return True

    @staticmethod
    def set_reset_token(
        db: Session, email: str, reset_token: str, expires_at: datetime
    ) -> Optional[User]:
        """Set password reset token for a user.

        Args:
            db (Session): Database session
            email (str): User's email address
            reset_token (str): Generated reset token
            expires_at (datetime): Token expiration time

        Returns:
            Optional[User]: Updated user if found, None otherwise
        """
        user = UserRepository.get_user_by_email(db, email)
        if not user:
            return None

        user.reset_token = reset_token
        user.reset_token_expires = expires_at
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_user_by_reset_token(db: Session, reset_token: str) -> Optional[User]:
        """Get user by password reset token.

        Validates that the token exists and hasn't expired.

        Args:
            db (Session): Database session
            reset_token (str): Password reset token

        Returns:
            Optional[User]: User if token is valid and not expired, None otherwise
        """
        user = (
            db.query(User)
            .filter(
                User.reset_token == reset_token,
                User.reset_token_expires > datetime.now(timezone.utc),
            )
            .first()
        )
        return user

    @staticmethod
    def clear_reset_token(db: Session, user_id: int) -> Optional[User]:
        """Clear password reset token for a user.

        This should be called after successful password reset or
        when the token should be invalidated.

        Args:
            db (Session): Database session
            user_id (int): User's ID

        Returns:
            Optional[User]: Updated user if found, None otherwise
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        user.reset_token = None
        user.reset_token_expires = None
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_password(db: Session, user_id: int, new_password: str) -> Optional[User]:
        """Update user's password.

        Args:
            db (Session): Database session
            user_id (int): User's ID
            new_password (str): New plain text password (will be hashed)

        Returns:
            Optional[User]: Updated user if found, None otherwise
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        user.hashed_password = AuthService.get_password_hash(new_password)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_user_role(db: Session, user_id: int, new_role: str) -> Optional[User]:
        """Update user's role.

        Args:
            db (Session): Database session
            user_id (int): User's ID
            new_role (str): New role (user, moderator, admin)

        Returns:
            Optional[User]: Updated user if found, None otherwise
        """
        from src.database.models import UserRole

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        try:
            # Convert string to UserRole enum
            role_enum = UserRole(new_role)
            user.role = role_enum
            db.commit()
            db.refresh(user)
            return user
        except ValueError:
            # Invalid role value
            return None

    @staticmethod
    def get_users_by_role(
        db: Session, role: str, skip: int = 0, limit: int = 100
    ) -> list[User]:
        """Get users by role with pagination.

        Args:
            db (Session): Database session
            role (str): Role to filter by
            skip (int): Number of records to skip
            limit (int): Maximum number of records to return

        Returns:
            List[User]: List of users with specified role
        """
        from src.database.models import UserRole

        try:
            role_enum = UserRole(role)
            return (
                db.query(User)
                .filter(User.role == role_enum)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except ValueError:
            return []

    @staticmethod
    def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
        """Get all users with pagination.

        Args:
            db (Session): Database session
            skip (int): Number of records to skip
            limit (int): Maximum number of records to return

        Returns:
            List[User]: List of all users
        """
        return db.query(User).offset(skip).limit(limit).all()

    @staticmethod
    def get_users_count(db: Session) -> int:
        """Get total number of users.

        Args:
            db (Session): Database session

        Returns:
            int: Total number of users
        """
        return db.query(User).count()

    @staticmethod
    def update_user_status(
        db: Session, user_id: int, is_active: bool
    ) -> Optional[User]:
        """Update user's active status.

        Args:
            db (Session): Database session
            user_id (int): User's ID
            is_active (bool): New active status

        Returns:
            Optional[User]: Updated user if found, None otherwise
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        user.is_active = is_active
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def search_users(
        db: Session, search_term: str, skip: int = 0, limit: int = 100
    ) -> list[User]:
        """Search users by username or email.

        Args:
            db (Session): Database session
            search_term (str): Term to search for in username or email
            skip (int): Number of records to skip
            limit (int): Maximum number of records to return

        Returns:
            List[User]: List of matching users
        """
        from sqlalchemy import or_

        return (
            db.query(User)
            .filter(
                or_(
                    User.username.ilike(f"%{search_term}%"),
                    User.email.ilike(f"%{search_term}%"),
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
