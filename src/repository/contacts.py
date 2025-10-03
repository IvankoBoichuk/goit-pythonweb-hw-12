from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import date, timedelta

from src.database.models import Contact
from src.schemas import ContactCreate, ContactUpdate


class ContactRepository:
    def __init__(self, db: Session):
        self.db = db

    async def get_contacts(self, skip: int = 0, limit: int = 100) -> List[Contact]:
        """Get all contacts with pagination"""
        return self.db.query(Contact).offset(skip).limit(limit).all()

    async def get_contact_by_id(self, contact_id: int) -> Optional[Contact]:
        """Get contact by ID"""
        return self.db.query(Contact).filter(Contact.id == contact_id).first()

    async def get_contact_by_email(self, email: str) -> Optional[Contact]:
        """Get contact by email"""
        return self.db.query(Contact).filter(Contact.email == email).first()

    async def create_contact(self, contact: ContactCreate) -> Contact:
        """Create a new contact"""
        db_contact = Contact(
            first_name=contact.first_name,
            last_name=contact.last_name,
            email=contact.email,
            phone=contact.phone,
            birthday=contact.birthday,
            additional_info=contact.additional_info
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

    async def search_contacts(self, query: str) -> List[Contact]:
        """Search contacts by first name, last name, or email"""
        return self.db.query(Contact).filter(
            or_(
                Contact.first_name.ilike(f"%{query}%"),
                Contact.last_name.ilike(f"%{query}%"),
                Contact.email.ilike(f"%{query}%")
            )
        ).all()

    async def get_upcoming_birthdays(self, days_ahead: int = 7) -> List[Contact]:
        """Get contacts with birthdays in the next N days"""
        today = date.today()
        future_date = today + timedelta(days=days_ahead)
        
        return self.db.query(Contact).filter(
            and_(
                Contact.birthday >= today,
                Contact.birthday <= future_date
            )
        ).all()