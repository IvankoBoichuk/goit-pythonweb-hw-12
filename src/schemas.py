from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional, List
from enum import Enum


# Role enum for API responses
class UserRoleEnum(str, Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool = True
    role: Optional[UserRoleEnum] = None

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# Contact schemas
class ContactBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    birthday: date
    additional_info: Optional[str] = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(ContactBase):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    birthday: Optional[date] = None
    phone: Optional[str] = None


class ContactResponse(ContactBase):
    id: int

    class Config:
        from_attributes = True


# Password reset schemas
class PasswordResetRequest(BaseModel):
    """Schema for requesting a password reset"""

    email: EmailStr


class PasswordReset(BaseModel):
    """Schema for resetting password with token"""

    token: str
    new_password: str


# Role management schemas
class UserRoleUpdate(BaseModel):
    """Schema for updating user role"""

    role: UserRoleEnum


class AdminUserResponse(BaseModel):
    """Extended user response schema for admin operations"""

    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    is_verified: bool
    role: UserRoleEnum
    avatar_url: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserStatusUpdate(BaseModel):
    """Schema for updating user account status"""

    is_active: bool
    reason: Optional[str] = None  # Reason for status change


class AdminAction(BaseModel):
    """Schema for logging admin actions"""

    action: str
    target_user_id: int
    details: Optional[str] = None
