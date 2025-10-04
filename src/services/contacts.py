from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status
import logging

from src.repository.contacts import ContactRepository
from src.schemas import ContactCreate, ContactUpdate, ContactResponse
from src.database.models import Contact
from src.services.cache import cache_service

logger = logging.getLogger(__name__)


class ContactService:
    def __init__(self, db: Session):
        self.repository = ContactRepository(db)

    async def get_contacts(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Contact]:
        """Get all contacts with pagination and caching"""
        # Спочатку перевіряємо кеш (лише для повного списку без пагінації)
        if skip == 0 and limit >= 100:
            cached_contacts = cache_service.get_contacts_cache(user_id)
            if cached_contacts:
                logger.debug(f"Contacts for user {user_id} retrieved from cache")
                # Конвертуємо кешовані дані в об'єкти Contact
                contacts = []
                for contact_data in cached_contacts:
                    contact = Contact()
                    for key, value in contact_data.items():
                        if key == 'birthday' and value:
                            from datetime import datetime
                            setattr(contact, key, datetime.fromisoformat(value).date())
                        else:
                            setattr(contact, key, value)
                    contacts.append(contact)
                return contacts[skip:skip+limit] if limit < len(contacts) else contacts[skip:]
        
        # Отримуємо з БД
        contacts = await self.repository.get_contacts_by_user(user_id, skip, limit)
        
        # Кешуємо повний список (без пагінації) для майбутніх запитів
        if skip == 0 and contacts:
            cache_service.set_contacts_cache(user_id, contacts)
            logger.debug(f"Contacts for user {user_id} cached after DB query")
        
        return contacts

    async def get_contact(self, contact_id: int) -> Optional[Contact]:
        """Get a specific contact by ID"""
        return await self.repository.get_contact_by_id(contact_id)

    async def create_contact(self, contact: ContactCreate, user_id: int) -> Contact:
        """Create a new contact and invalidate cache"""
        # Check if email already exists for this user
        existing_contact = await self.repository.get_contact_by_email(contact.email, user_id)
        if existing_contact:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contact with this email already exists"
            )
        
        # Додаємо user_id до контакту
        contact_data = contact.dict()
        contact_data['user_id'] = user_id
        
        new_contact = await self.repository.create_contact(ContactCreate(**contact_data))
        
        if new_contact:
            # Інвалідуємо кеш контактів користувача
            cache_service.invalidate_contacts_cache(user_id)
            logger.debug(f"Contacts cache invalidated for user {user_id} after creating contact")
        
        return new_contact

    async def update_contact(self, contact_id: int, contact: ContactUpdate, user_id: int) -> Optional[Contact]:
        """Update an existing contact and invalidate cache"""
        # Check if contact exists and belongs to user
        existing_contact = await self.repository.get_contact_by_id(contact_id)
        if not existing_contact or existing_contact.user_id != user_id:
            return None
        
        # Check if email is being changed and if new email already exists
        if contact.email and contact.email != existing_contact.email:
            email_exists = await self.repository.get_contact_by_email(contact.email, user_id)
            if email_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Contact with this email already exists"
                )
        
        updated_contact = await self.repository.update_contact(contact_id, contact)
        
        if updated_contact:
            # Інвалідуємо кеш контактів користувача
            cache_service.invalidate_contacts_cache(user_id)
            logger.debug(f"Contacts cache invalidated for user {user_id} after updating contact {contact_id}")
        
        return updated_contact
    
    async def delete_contact(self, contact_id: int, user_id: int) -> bool:
        """Delete contact and invalidate cache"""
        # Перевіряємо чи контакт існує та належить користувачу
        existing_contact = await self.repository.get_contact_by_id(contact_id)
        if not existing_contact or existing_contact.user_id != user_id:
            return False
        
        deleted = await self.repository.delete_contact(contact_id)
        
        if deleted:
            # Інвалідуємо кеш контактів користувача
            cache_service.invalidate_contacts_cache(user_id)
            logger.debug(f"Contacts cache invalidated for user {user_id} after deleting contact {contact_id}")
        
        return deleted

    async def search_contacts(self, query: str, user_id: int) -> List[Contact]:
        """Search contacts by first name, last name, or email for specific user"""
        if not query.strip():
            return []
        return await self.repository.search_contacts(query, user_id)

    async def get_upcoming_birthdays(self, days_ahead: int = 7, user_id: int = None) -> List[Contact]:
        """Get contacts with birthdays in the next N days for specific user"""
        if days_ahead < 0:
            days_ahead = 7
        return await self.repository.get_upcoming_birthdays(days_ahead, user_id)