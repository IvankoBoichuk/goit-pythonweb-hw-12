from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List

from src.database.db import get_db
from src.database.models import User
from src.schemas import ContactCreate, ContactUpdate, ContactResponse
from src.services.contacts import ContactService
from src.services.auth import get_current_active_user

# Create router
router = APIRouter()

@router.get("/contacts", response_model=List[ContactResponse])
async def get_contacts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieve all contacts for the authenticated user with pagination.
    
    Args:
        skip (int, optional): Number of records to skip for pagination. Defaults to 0.
        limit (int, optional): Maximum number of records to return. Defaults to 100.
        db (Session): Database session dependency
        current_user (User): Currently authenticated user
        
    Returns:
        List[ContactResponse]: List of contacts belonging to the current user
        
    Raises:
        HTTPException: 401 if user is not authenticated
        HTTPException: 500 if database error occurs
    """
    service = ContactService(db)
    contacts = await service.get_contacts(user_id=current_user.id, skip=skip, limit=limit)
    return contacts

@router.get("/contacts/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific contact by ID"""
    service = ContactService(db)
    contact = await service.get_contact(contact_id, user_id=current_user.id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    return contact

@router.post("/contacts", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new contact"""
    service = ContactService(db)
    return await service.create_contact(contact, user_id=current_user.id)

@router.put("/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    contact: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an existing contact"""
    service = ContactService(db)
    updated_contact = await service.update_contact(contact_id, contact, user_id=current_user.id)
    if not updated_contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    return updated_contact

@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a contact"""
    service = ContactService(db)
    deleted = await service.delete_contact(contact_id, user_id=current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )

@router.get("/contacts/search/{query}", response_model=List[ContactResponse])
async def search_contacts(
    query: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Search contacts by first name, last name, or email"""
    service = ContactService(db)
    contacts = await service.search_contacts(query, user_id=current_user.id)
    return contacts

@router.get("/contacts/birthdays/upcoming", response_model=List[ContactResponse])
async def get_upcoming_birthdays(
    days_ahead: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get contacts with birthdays in the next N days (default 7)"""
    service = ContactService(db)
    contacts = await service.get_upcoming_birthdays(days_ahead, user_id=current_user.id)
    return contacts