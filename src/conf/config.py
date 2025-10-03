import os
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseModel):
    # JWT Settings
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:567234@postgres:5432/hw12")
    
    # App settings
    app_name: str = "Contacts API"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Rate limiting settings
    rate_limit_enabled: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Rate limits per endpoint
    auth_me_rate_limit: str = os.getenv("AUTH_ME_RATE_LIMIT", "10/minute")  # 10 requests per minute
    
    # CORS settings
    cors_origins: list = os.getenv("CORS_ORIGINS", "*").split(",")
    cors_allow_credentials: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "True").lower() == "true"
    cors_allow_methods: list = os.getenv("CORS_ALLOW_METHODS", "GET,POST,PUT,DELETE,OPTIONS").split(",")
    cors_allow_headers: list = os.getenv("CORS_ALLOW_HEADERS", "*").split(",")
    
    # Cloudinary settings
    cloudinary_name: str = os.getenv("CLOUDINARY_NAME", "")
    cloudinary_api_key: str = os.getenv("CLOUDINARY_API_KEY", "")
    cloudinary_api_secret: str = os.getenv("CLOUDINARY_API_SECRET", "")
    
    # File upload settings
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "5242880"))  # 5MB default
    allowed_image_types: list = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    
    # Email settings (SMTP)
    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    from_email: str = os.getenv("FROM_EMAIL", "")


settings = Settings()
