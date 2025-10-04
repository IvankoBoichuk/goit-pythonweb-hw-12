from sqlalchemy import Column, Integer, String, Date, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from .db import Base

class User(Base):
    """User model for authentication and profile management.
    
    Represents a user in the system with authentication credentials,
    profile information, and email verification status.
    
    Attributes:
        id (int): Primary key
        username (str): Unique username for login
        email (str): Unique email address
        hashed_password (str): PBKDF2-SHA256 hashed password
        full_name (str, optional): User's full display name
        is_active (bool): Account active status, defaults to True
        is_verified (bool): Email verification status, defaults to False
        verification_token (str, optional): Token for email verification
        avatar_url (str, optional): URL to user's avatar image
        contacts (List[Contact]): Related contacts owned by this user
    """
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # Email verification status
    verification_token = Column(String(255), nullable=True)  # Email verification token
    avatar_url = Column(String(500), nullable=True)  # URL to avatar image
    reset_token = Column(String(255), nullable=True)  # Password reset token
    reset_token_expires = Column(DateTime, nullable=True)  # Password reset token expiration
    
    # Relationship with contacts
    contacts = relationship("Contact", back_populates="owner")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

class Contact(Base):
    """Contact model for storing personal contact information.
    
    Represents a contact entry belonging to a specific user with
    personal details and birthday information.
    
    Attributes:
        id (int): Primary key
        first_name (str): Contact's first name
        last_name (str): Contact's last name
        email (str): Contact's email address (not unique across users)
        phone (str): Contact's phone number
        birthday (date): Contact's birthday date
        additional_info (str, optional): Additional notes about the contact
        user_id (int): Foreign key linking to the owning user
        owner (User): Relationship to the User who owns this contact
    """
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False, index=True)
    last_name = Column(String(50), nullable=False, index=True)
    email = Column(String(100), nullable=False, index=True)  # Remove unique=True to allow multiple users to have contacts with same email
    phone = Column(String(20), nullable=False)
    birthday = Column(Date, nullable=False)
    additional_info = Column(Text, nullable=True)
    
    # Foreign key to link contact to user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationship
    owner = relationship("User", back_populates="contacts")
    
    def __repr__(self):
        return f"<Contact(id={self.id}, first_name='{self.first_name}', last_name='{self.last_name}', email='{self.email}')>"