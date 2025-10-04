from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import date, timedelta

from src.database.models import Contact
from src.schemas import ContactCreate, ContactUpdate


class ContactRepository:
    """Repository for contact data access operations.
    
    Provides async methods for CRUD operations on contacts with proper
    database session management and user context isolation.
    
    Attributes:
        db (Session): SQLAlchemy database session
    """
    
    def __init__(self, db: Session):
        """Initialize repository with database session.
        
        Args:
            db (Session): SQLAlchemy database session
        """
        self.db = db

    async def get_contacts(self, skip: int = 0, limit: int = 100) -> List[Contact]:
        """Retrieve contacts with pagination support.
        
        Args:
            skip (int, optional): Number of records to skip. Defaults to 0.
            limit (int, optional): Maximum number of records to return. Defaults to 100.
            
        Returns:
            List[Contact]: List of contact objects
            
        Note:
            This method should be called with user filtering to ensure
            proper data isolation between users.
        """
        return self.db.query(Contact).offset(skip).limit(limit).all()

    async def get_contact_by_id(self, contact_id: int) -> Optional[Contact]:
        """Get contact by ID"""
        return self.db.query(Contact).filter(Contact.id == contact_id).first()

    async def get_contact_by_email(self, email: str, user_id: int = None) -> Optional[Contact]:
        """Get contact by email, optionally filtered by user"""
        query = self.db.query(Contact).filter(Contact.email == email)
        if user_id is not None:
            query = query.filter(Contact.user_id == user_id)
        return query.first()
    
    async def get_contacts_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Contact]:
        """Get all contacts for a specific user with pagination"""
        return (self.db.query(Contact)
                .filter(Contact.user_id == user_id)
                .offset(skip)
                .limit(limit)
                .all())

    async def create_contact(self, contact: ContactCreate) -> Contact:
        """Create a new contact in the database.
        
        Args:
            contact (ContactCreate): Pydantic model with contact data
            
        Returns:
            Contact: The created contact object with assigned ID
            
        Raises:
            SQLAlchemyError: If database operation fails
            
        Note:
            The user_id field must be set separately by the calling service
            to ensure proper user context isolation.
        """
        db_contact = Contact(
            first_name=contact.first_name,
            last_name=contact.last_name,
            email=contact.email,
            phone=contact.phone,
            birthday=contact.birthday,
            additional_info=contact.additional_info,
            user_id=getattr(contact, 'user_id', None)
        )
        self.db.add(db_contact)
        self.db.commit()
        self.db.refresh(db_contact)
        return db_contact

    async def update_contact(self, contact_id: int, contact: ContactUpdate) -> Optional[Contact]:
        """Update an existing contact"""
        db_contact = self.db.query(Contact).filter(Contact.id == contact_id).first()
        if db_contact:
            update_data = contact.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_contact, field, value)
            self.db.commit()
            self.db.refresh(db_contact)
        return db_contact

    async def delete_contact(self, contact_id: int) -> bool:
        """Delete a contact"""
        db_contact = self.db.query(Contact).filter(Contact.id == contact_id).first()
        if db_contact:
            self.db.delete(db_contact)
            self.db.commit()
            return True
        return False

    async def search_contacts(self, query: str, user_id: int) -> List[Contact]:
        """Search contacts by first name, last name, or email for specific user"""
        return self.db.query(Contact).filter(
            Contact.user_id == user_id,
            or_(
                Contact.first_name.ilike(f"%{query}%"),
                Contact.last_name.ilike(f"%{query}%"),
                Contact.email.ilike(f"%{query}%")
            )
        ).all()

    async def get_upcoming_birthdays(self, days_ahead: int = 7, user_id: int = None) -> List[Contact]:
        """Get contacts with birthdays in the next N days for specific user"""
        today = date.today()
        future_date = today + timedelta(days=days_ahead)
        
        query = self.db.query(Contact).filter(
            and_(
                Contact.birthday >= today,
                Contact.birthday <= future_date
            )
        )
        
        if user_id:
            query = query.filter(Contact.user_id == user_id)
            
        return query.all()