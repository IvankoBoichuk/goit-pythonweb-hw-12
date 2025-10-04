from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from src.conf.config import settings
from src.database.db import get_db
from src.database.models import User
from src.schemas import TokenData

# Password context for hashing - using pbkdf2_sha256 as alternative to bcrypt
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# OAuth2 scheme
security = HTTPBearer()


class AuthService:
    """Authentication service for handling password hashing, JWT tokens, and user verification.

    This service provides static methods for:
    - Password hashing and verification using PBKDF2-SHA256
    - JWT access token creation and verification
    - Email verification token generation
    """

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain text password against its hash.

        Args:
            plain_password (str): The plain text password to verify
            hashed_password (str): The hashed password to compare against

        Returns:
            bool: True if password matches hash, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate a secure hash for a plain text password.

        Uses PBKDF2-SHA256 algorithm for password hashing.

        Args:
            password (str): The plain text password to hash

        Returns:
            str: The hashed password string
        """
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create a JWT access token with expiration.

        Args:
            data (dict): The payload data to encode in the token
            expires_delta (Optional[timedelta]): Custom expiration time.
                If None, uses default from settings.

        Returns:
            str: The encoded JWT access token

        Note:
            Token includes 'exp' claim for expiration time and is signed with
            the application's secret key using HS256 algorithm.
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.access_token_expire_minutes
            )

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.secret_key, algorithm=settings.algorithm
        )
        return encoded_jwt

    @staticmethod
    def verify_token(token: str, credentials_exception):
        """Verify JWT token and extract username."""
        try:
            payload = jwt.decode(
                token, settings.secret_key, algorithms=[settings.algorithm]
            )
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            token_data = TokenData(username=username)
            return token_data
        except JWTError:
            raise credentials_exception

    @staticmethod
    def create_verification_token() -> str:
        """Create a unique verification token."""
        return str(uuid.uuid4())

    @staticmethod
    def create_email_verification_token(
        data: dict, expires_delta: Optional[timedelta] = None
    ):
        """Create JWT token for email verification."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                hours=24
            )  # 24 hours for email verification

        to_encode.update({"exp": expire, "purpose": "email_verification"})
        encoded_jwt = jwt.encode(
            to_encode, settings.secret_key, algorithm=settings.algorithm
        )
        return encoded_jwt

    @staticmethod
    def verify_email_token(token: str):
        """Verify email verification token and extract data."""
        try:
            payload = jwt.decode(
                token, settings.secret_key, algorithms=[settings.algorithm]
            )
            purpose = payload.get("purpose")
            if purpose != "email_verification":
                return None
            email = payload.get("sub")
            if email is None:
                return None
            return email
        except JWTError:
            return None

    @staticmethod
    def generate_reset_token() -> str:
        """Generate a secure password reset token.

        Creates a UUID4 token for password reset that will be stored
        in the database and sent via email.

        Returns:
            str: A unique password reset token
        """
        return str(uuid.uuid4())

    @staticmethod
    def create_password_reset_token(
        data: dict, expires_delta: Optional[timedelta] = None
    ):
        """Create JWT token for password reset verification.

        This token is used to verify the password reset request and
        contains the user's email and purpose identification.

        Args:
            data (dict): Token payload containing user information
            expires_delta (Optional[timedelta]): Custom expiration time.
                Defaults to 1 hour for security.

        Returns:
            str: Encoded JWT token for password reset
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                hours=1
            )  # 1 hour for password reset

        to_encode.update({"exp": expire, "purpose": "password_reset"})
        encoded_jwt = jwt.encode(
            to_encode, settings.secret_key, algorithm=settings.algorithm
        )
        return encoded_jwt

    @staticmethod
    def verify_password_reset_token(token: str):
        """Verify password reset token and extract email.

        Validates the JWT token and ensures it's a password reset token
        that hasn't expired.

        Args:
            token (str): The JWT token to verify

        Returns:
            str | None: User's email if token is valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token, settings.secret_key, algorithms=[settings.algorithm]
            )
            purpose = payload.get("purpose")
            if purpose != "password_reset":
                return None
            email = payload.get("sub")
            if email is None:
                return None
            return email
        except JWTError:
            return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    token_data = AuthService.verify_token(token, credentials_exception)

    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_verified_user(current_user: User = Depends(get_current_active_user)):
    """Get the current verified user (email verified)."""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your email and verify your account.",
        )
    return current_user


# Role-based authentication functions


def require_role(required_role: str):
    """Decorator factory for role-based access control with caching.

    Args:
        required_role (str): The minimum required role (user, moderator, admin)

    Returns:
        Function: Dependency function that checks user role
    """

    def role_dependency(current_user: User = Depends(get_current_active_user)):
        from src.services.cache import cache_service

        # Try cache first for performance
        cached_permission = cache_service.check_role_permission(
            current_user.id, required_role
        )

        if cached_permission is not None:
            if not cached_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required role: {required_role}, your role: {current_user.role.value}",
                )
            return current_user

        # Cache miss - check role and update cache
        role_hierarchy = {"user": 1, "moderator": 2, "admin": 3}

        user_role_level = role_hierarchy.get(current_user.role.value, 0)
        required_role_level = role_hierarchy.get(required_role, 999)

        # Cache the user's role for future checks
        cache_service.cache_user_role(current_user.id, current_user.role.value)

        if user_role_level < required_role_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role}, your role: {current_user.role.value}",
            )
        return current_user

    return role_dependency


def get_current_admin(current_user: User = Depends(get_current_active_user)):
    """Get current user if they have admin role.

    Raises:
        HTTPException: If user is not admin

    Returns:
        User: Current user with admin privileges
    """
    from src.database.models import UserRole

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user


def get_current_moderator(current_user: User = Depends(get_current_active_user)):
    """Get current user if they have moderator or admin role.

    Raises:
        HTTPException: If user is not moderator or admin

    Returns:
        User: Current user with moderator+ privileges
    """
    from src.database.models import UserRole

    allowed_roles = [UserRole.MODERATOR, UserRole.ADMIN]
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Moderator access required"
        )
    return current_user


def check_user_role(user: User, required_role: str) -> bool:
    """Check if user has sufficient role privileges.

    Args:
        user (User): User to check
        required_role (str): Required role level

    Returns:
        bool: True if user has sufficient privileges
    """
    role_hierarchy = {"user": 1, "moderator": 2, "admin": 3}

    user_role_level = role_hierarchy.get(user.role.value, 0)
    required_role_level = role_hierarchy.get(required_role, 999)

    return user_role_level >= required_role_level


def require_admin_or_self(target_user_id: int):
    """Dependency that allows access if user is admin or accessing their own data.

    Args:
        target_user_id (int): ID of the user being accessed

    Returns:
        Function: Dependency function
    """

    def admin_or_self_dependency(current_user: User = Depends(get_current_active_user)):
        from src.database.models import UserRole

        # Allow if user is admin or accessing their own data
        if current_user.role == UserRole.ADMIN or current_user.id == target_user_id:
            return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin access required or you can only access your own data.",
        )

    return admin_or_self_dependency
