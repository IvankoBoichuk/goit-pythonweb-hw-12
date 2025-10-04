from typing import Optional
from sqlalchemy.orm import Session
from src.database.models import User
from src.schemas import UserCreate
from src.repository.users import UserRepository
from src.services.cache import cache_service
import logging

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository()
    
    async def create_user(self, user: UserCreate) -> User:
        """Create a new user and cache it."""
        new_user = self.user_repository.create_user(self.db, user)
        if new_user:
            # Кешуємо нового користувача
            cache_service.set_user_cache(new_user)
            logger.debug(f"New user {new_user.id} cached after creation")
        return new_user
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username with caching."""
        # Спробуємо отримати з кешу
        cached_data = cache_service.get_user_by_username(username)
        if cached_data:
            logger.debug(f"User {username} retrieved from cache")
            # Створюємо об'єкт User з кешованих даних
            user = User()
            for key, value in cached_data.items():
                setattr(user, key, value)
            return user
        
        # Якщо не знайдено в кеші, отримуємо з БД
        user = self.user_repository.get_user_by_username(self.db, username)
        if user:
            # Кешуємо користувача
            cache_service.set_user_cache(user)
            logger.debug(f"User {username} cached after DB query")
        
        return user
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email with caching."""
        # Спробуємо отримати з кешу
        cached_data = cache_service.get_user_by_email(email)
        if cached_data:
            logger.debug(f"User {email} retrieved from cache")
            # Створюємо об'єкт User з кешованих даних
            user = User()
            for key, value in cached_data.items():
                setattr(user, key, value)
            return user
        
        # Якщо не знайдено в кеші, отримуємо з БД
        user = self.user_repository.get_user_by_email(self.db, email)
        if user:
            # Кешуємо користувача
            cache_service.set_user_cache(user)
            logger.debug(f"User {email} cached after DB query")
        
        return user
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID with caching."""
        # Спробуємо отримати з кешу
        cached_data = cache_service.get_user_by_id(user_id)
        if cached_data:
            logger.debug(f"User {user_id} retrieved from cache")
            # Створюємо об'єкт User з кешованих даних
            user = User()
            for key, value in cached_data.items():
                setattr(user, key, value)
            return user
        
        # Якщо не знайдено в кеші, отримуємо з БД
        user = self.user_repository.get_user_by_id(self.db, user_id)
        if user:
            # Кешуємо користувача
            cache_service.set_user_cache(user)
            logger.debug(f"User {user_id} cached after DB query")
        
        return user
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user."""
        return self.user_repository.authenticate_user(self.db, username, password)
    
    async def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user and invalidate cache."""
        # Отримуємо користувача перед оновленням для інвалідації кешу
        old_user = await self.get_user_by_id(user_id)
        if not old_user:
            return None
        
        # Оновлюємо користувача в БД
        updated_user = self.user_repository.update_user(self.db, user_id, **kwargs)
        
        if updated_user:
            # Інвалідуємо старий кеш
            cache_service.invalidate_user_cache(old_user)
            
            # Кешуємо оновлені дані
            cache_service.set_user_cache(updated_user)
            logger.debug(f"User {user_id} cache updated after modification")
        
        return updated_user
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete user and clear all cache."""
        # Отримуємо користувача для очищення кешу
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Видаляємо з БД
        deleted = self.user_repository.delete_user(self.db, user_id)
        
        if deleted:
            # Очищаємо весь кеш користувача (профіль + контакти)
            cache_service.clear_user_all_cache(user_id)
            logger.info(f"User {user_id} deleted and cache cleared")
        
        return deleted