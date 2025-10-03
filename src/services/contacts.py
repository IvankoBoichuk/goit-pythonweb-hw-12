from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status

from src.repository.contacts import ContactRepository
from src.schemas import ContactCreate, ContactUpdate, ContactResponse
from src.database.models import Contact


class ContactService:
    def __init__(self, db: Session):
        self.repository = ContactRepository(db)

    async def get_contacts(self, skip: int = 0, limit: int = 100) -> List[Contact]:
        """Get all contacts with pagination"""
        return await self.repository.get_contacts(skip, limit)

    async def get_contact(self, contact_id: int) -> Optional[Contact]:
        """Get a specific contact by ID"""
        return await self.repository.get_contact_by_id(contact_id)

    async def create_contact(self, contact: ContactCreate) -> Contact:
        """Create a new contact"""
        # Check if email already exists
        existing_contact = await self.repository.get_contact_by_email(contact.email)
        if existing_contact:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contact with this email already exists"
            )
        
        return await self.repository.create_contact(contact)

    async def update_contact(self, contact_id: int, contact: ContactUpdate) -> Optional[Contact]:
        """Update an existing contact"""
        # Check if contact exists
        existing_contact = await self.repository.get_contact_by_id(contact_id)
        if not existing_contact:
            return None
        
        # Check if email is being changed and if new email already exists
        if contact.email and contact.email != existing_contact.email:
            email_exists = await self.repository.get_contact_by_email(contact.email)
            if email_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Contact with this email already exists"
                )
        
        return await self.repository.update_contact(contact_id, contact)

    async def delete_contact(self, contact_id: int) -> bool:
        """Delete a contact"""
        return await self.repository.delete_contact(contact_id)

    async def search_contacts(self, query: str) -> List[Contact]:
        """Search contacts by first name, last name, or email"""
        if not query.strip():
            return []
        return await self.repository.search_contacts(query)

    async def get_upcoming_birthdays(self, days_ahead: int = 7) -> List[Contact]:
        """Get contacts with birthdays in the next N days"""
        if days_ahead < 0:
            days_ahead = 7
        return await self.repository.get_upcoming_birthdays(days_ahead)