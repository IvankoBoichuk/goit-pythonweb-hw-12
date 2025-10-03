from typing import Optional
from sqlalchemy.orm import Session
from src.database.models import User
from src.schemas import UserCreate
from src.repository.users import UserRepository


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository()
    
    async def create_user(self, user: UserCreate) -> User:
        """Create a new user."""
        return self.user_repository.create_user(self.db, user)
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.user_repository.get_user_by_username(self.db, username)
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.user_repository.get_user_by_email(self.db, email)
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user."""
        return self.user_repository.authenticate_user(self.db, username, password)