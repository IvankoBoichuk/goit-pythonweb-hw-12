"""Redis кешування сервіс для користувачів та контактів."""

import json
import redis
from typing import Optional, Any, Dict, List
from datetime import timedelta
import logging
from src.conf.config import settings
from src.database.models import User, Contact

logger = logging.getLogger(__name__)


class CacheService:
    """Сервіс для кешування даних користувачів та контактів з Redis."""
    
    def __init__(self):
        """Ініціалізація Redis клієнта з fallback."""
        self.redis_client = None
        self.cache_enabled = settings.rate_limit_enabled
        
        if self.cache_enabled:
            try:
                self.redis_client = redis.Redis.from_url(
                    settings.redis_url, 
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
                # Тест підключення
                self.redis_client.ping()
                logger.info("Redis cache service initialized successfully")
            except (redis.ConnectionError, redis.TimeoutError) as e:
                logger.warning(f"Redis cache unavailable: {e}. Caching disabled.")
                self.redis_client = None
                self.cache_enabled = False
    
    def _generate_key(self, prefix: str, identifier: str) -> str:
        """Генерує ключ для кешу з префіксом."""
        return f"{settings.app_name}:{prefix}:{identifier}"
    
    def _serialize_user(self, user: User) -> Dict[str, Any]:
        """Серіалізує об'єкт користувача для кешування."""
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "avatar_url": user.avatar_url,
            "hashed_password": user.hashed_password  # Потрібно для аутентифікації
        }
    
    def _deserialize_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Десеріалізує дані користувача з кешу."""
        return data
    
    def _serialize_contact(self, contact: Contact) -> Dict[str, Any]:
        """Серіалізує об'єкт контакту для кешування."""
        return {
            "id": contact.id,
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "email": contact.email,
            "phone": contact.phone,
            "birthday": contact.birthday.isoformat() if contact.birthday else None,
            "additional_info": contact.additional_info,
            "user_id": contact.user_id
        }
    
    # === Методи для користувачів ===
    
    def set_user_cache(self, user: User, ttl: timedelta = timedelta(hours=1)) -> bool:
        """Кешує користувача за ID, username та email."""
        if not self.cache_enabled or not self.redis_client:
            return False
            
        try:
            user_data = self._serialize_user(user)
            user_json = json.dumps(user_data)
            ttl_seconds = int(ttl.total_seconds())
            
            # Кешування за різними ключами для швидкого пошуку
            keys = [
                self._generate_key("user_id", str(user.id)),
                self._generate_key("user_username", user.username),
                self._generate_key("user_email", user.email)
            ]
            
            pipeline = self.redis_client.pipeline()
            for key in keys:
                pipeline.setex(key, ttl_seconds, user_json)
            pipeline.execute()
            
            logger.debug(f"User {user.id} cached successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache user {user.id}: {e}")
            return False
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Отримує користувача з кешу за ID."""
        if not self.cache_enabled or not self.redis_client:
            return None
            
        try:
            key = self._generate_key("user_id", str(user_id))
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                logger.debug(f"User {user_id} found in cache")
                return self._deserialize_user(json.loads(cached_data))
                
        except Exception as e:
            logger.error(f"Failed to get user {user_id} from cache: {e}")
            
        return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Отримує користувача з кешу за username."""
        if not self.cache_enabled or not self.redis_client:
            return None
            
        try:
            key = self._generate_key("user_username", username)
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                logger.debug(f"User {username} found in cache")
                return self._deserialize_user(json.loads(cached_data))
                
        except Exception as e:
            logger.error(f"Failed to get user {username} from cache: {e}")
            
        return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Отримує користувача з кешу за email."""
        if not self.cache_enabled or not self.redis_client:
            return None
            
        try:
            key = self._generate_key("user_email", email)
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                logger.debug(f"User {email} found in cache")
                return self._deserialize_user(json.loads(cached_data))
                
        except Exception as e:
            logger.error(f"Failed to get user {email} from cache: {e}")
            
        return None
    
    def invalidate_user_cache(self, user: User) -> bool:
        """Інвалідує кеш користувача."""
        if not self.cache_enabled or not self.redis_client:
            return False
            
        try:
            keys = [
                self._generate_key("user_id", str(user.id)),
                self._generate_key("user_username", user.username),
                self._generate_key("user_email", user.email)
            ]
            
            deleted = self.redis_client.delete(*keys)
            logger.debug(f"Invalidated {deleted} cache entries for user {user.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to invalidate user {user.id} cache: {e}")
            return False
    
    # === Методи для контактів ===
    
    def set_contacts_cache(self, user_id: int, contacts: List[Contact], 
                          ttl: timedelta = timedelta(minutes=30)) -> bool:
        """Кешує список контактів користувача."""
        if not self.cache_enabled or not self.redis_client:
            return False
            
        try:
            contacts_data = [self._serialize_contact(contact) for contact in contacts]
            contacts_json = json.dumps(contacts_data)
            
            key = self._generate_key("user_contacts", str(user_id))
            ttl_seconds = int(ttl.total_seconds())
            
            self.redis_client.setex(key, ttl_seconds, contacts_json)
            logger.debug(f"Cached {len(contacts)} contacts for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache contacts for user {user_id}: {e}")
            return False
    
    def get_contacts_cache(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """Отримує список контактів користувача з кешу."""
        if not self.cache_enabled or not self.redis_client:
            return None
            
        try:
            key = self._generate_key("user_contacts", str(user_id))
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                contacts_data = json.loads(cached_data)
                logger.debug(f"Found {len(contacts_data)} cached contacts for user {user_id}")
                return contacts_data
                
        except Exception as e:
            logger.error(f"Failed to get contacts for user {user_id} from cache: {e}")
            
        return None
    
    def invalidate_contacts_cache(self, user_id: int) -> bool:
        """Інвалідує кеш контактів користувача."""
        if not self.cache_enabled or not self.redis_client:
            return False
            
        try:
            key = self._generate_key("user_contacts", str(user_id))
            deleted = self.redis_client.delete(key)
            logger.debug(f"Invalidated contacts cache for user {user_id}")
            return deleted > 0
            
        except Exception as e:
            logger.error(f"Failed to invalidate contacts cache for user {user_id}: {e}")
            return False
    
    # === Загальні методи ===
    
    def clear_user_all_cache(self, user_id: int) -> bool:
        """Очищає весь кеш для користувача (профіль + контакти)."""
        try:
            # Отримуємо користувача для інвалідації всіх його ключів
            user_data = self.get_user_by_id(user_id)
            if user_data:
                # Створюємо фіктивний об'єкт для інвалідації
                class MockUser:
                    def __init__(self, data):
                        self.id = data['id']
                        self.username = data['username']
                        self.email = data['email']
                
                mock_user = MockUser(user_data)
                self.invalidate_user_cache(mock_user)
            
            # Інвалідуємо кеш контактів
            self.invalidate_contacts_cache(user_id)
            
            logger.info(f"Cleared all cache for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear cache for user {user_id}: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Отримує статистику кешу."""
        if not self.cache_enabled or not self.redis_client:
            return {"enabled": False, "error": "Cache disabled or unavailable"}
            
        try:
            info = self.redis_client.info()
            return {
                "enabled": True,
                "connected_clients": info.get('connected_clients', 0),
                "used_memory": info.get('used_memory_human', '0B'),
                "keyspace_hits": info.get('keyspace_hits', 0),
                "keyspace_misses": info.get('keyspace_misses', 0),
                "redis_version": info.get('redis_version', 'unknown')
            }
        except Exception as e:
            return {"enabled": False, "error": str(e)}


# Глобальний екземпляр сервісу кешування
cache_service = CacheService()