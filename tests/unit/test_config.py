"""
Тести для конфігурації додатку.
"""

import pytest
import os
from unittest.mock import patch
from src.conf.config import Settings


class TestSettings:
    """Тести для Settings конфігурації."""

    def test_settings_default_values(self):
        """Тест значень за замовчуванням."""
        settings = Settings()

        assert settings.algorithm == "HS256"
        assert settings.access_token_expire_minutes == 30
        assert settings.app_name == "Contacts API"
        assert settings.max_file_size == 5242880  # 5MB
        assert settings.smtp_port == 587

    def test_settings_secret_key_default(self):
        """Тест значення за замовчуванням для secret_key."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert "your-secret-key-change-this-in-production" in settings.secret_key

    def test_settings_database_url_default(self):
        """Тест значення за замовчуванням для database_url."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert "postgresql+psycopg2" in settings.database_url
            assert "postgres:5432" in settings.database_url

    def test_settings_from_environment(self):
        """Тест читання налаштувань з змінних середовища."""
        test_env = {
            "SECRET_KEY": "test-secret-key",
            "DATABASE_URL": "postgresql://test:test@localhost:5432/testdb",
            "DEBUG": "true",
            "REDIS_URL": "redis://localhost:6380",
        }

        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()
            assert settings.secret_key == "test-secret-key"
            assert (
                settings.database_url == "postgresql://test:test@localhost:5432/testdb"
            )
            assert settings.debug is True
            assert settings.redis_url == "redis://localhost:6380"

    def test_settings_boolean_parsing(self):
        """Тест парсингу boolean значень."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("anything", False),
        ]

        for env_value, expected in test_cases:
            with patch.dict(os.environ, {"DEBUG": env_value}, clear=True):
                settings = Settings()
                assert settings.debug == expected

    def test_settings_cors_origins_parsing(self):
        """Тест парсингу CORS origins."""
        test_env = {
            "CORS_ORIGINS": "http://localhost:3000,https://example.com,https://app.example.com"
        }

        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()
            expected_origins = [
                "http://localhost:3000",
                "https://example.com",
                "https://app.example.com",
            ]
            assert settings.cors_origins == expected_origins

    def test_settings_cors_methods_parsing(self):
        """Тест парсингу CORS methods."""
        test_env = {"CORS_ALLOW_METHODS": "GET,POST,PUT"}

        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()
            assert settings.cors_allow_methods == ["GET", "POST", "PUT"]

    def test_settings_rate_limiting(self):
        """Тест налаштувань rate limiting."""
        test_env = {"RATE_LIMIT_ENABLED": "false", "AUTH_ME_RATE_LIMIT": "20/minute"}

        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()
            assert settings.rate_limit_enabled is False
            assert settings.auth_me_rate_limit == "20/minute"

    def test_settings_cloudinary_config(self):
        """Тест налаштувань Cloudinary."""
        test_env = {
            "CLOUDINARY_NAME": "test-cloud",
            "CLOUDINARY_API_KEY": "test-key",
            "CLOUDINARY_API_SECRET": "test-secret",
        }

        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()
            assert settings.cloudinary_name == "test-cloud"
            assert settings.cloudinary_api_key == "test-key"
            assert settings.cloudinary_api_secret == "test-secret"

    def test_settings_email_config(self):
        """Тест налаштувань email."""
        test_env = {
            "SMTP_SERVER": "smtp.example.com",
            "SMTP_PORT": "465",
            "SMTP_USERNAME": "test@example.com",
            "SMTP_PASSWORD": "testpass",
            "FROM_EMAIL": "noreply@example.com",
        }

        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()
            assert settings.smtp_server == "smtp.example.com"
            assert settings.smtp_port == 465
            assert settings.smtp_username == "test@example.com"
            assert settings.smtp_password == "testpass"
            assert settings.from_email == "noreply@example.com"

    def test_settings_file_upload_config(self):
        """Тест налаштувань завантаження файлів."""
        test_env = {"MAX_FILE_SIZE": "10485760"}  # 10MB

        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()
            assert settings.max_file_size == 10485760
            assert "image/jpeg" in settings.allowed_image_types
            assert "image/png" in settings.allowed_image_types

    def test_settings_instance_creation(self):
        """Тест створення екземпляру Settings."""
        settings1 = Settings()
        settings2 = Settings()

        # Кожен екземпляр повинен мати однакові значення
        assert settings1.algorithm == settings2.algorithm
        assert settings1.app_name == settings2.app_name

    def test_settings_model_validation(self):
        """Тест що Settings є валідною Pydantic моделлю."""
        settings = Settings()

        # Перевіримо що можна отримати dict
        settings_dict = settings.model_dump()
        assert isinstance(settings_dict, dict)
        assert "secret_key" in settings_dict
        assert "database_url" in settings_dict

    def test_settings_default_cors_headers(self):
        """Тест значень за замовчуванням для CORS headers."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert "*" in settings.cors_allow_headers

    def test_settings_integer_conversion(self):
        """Тест конвертації рядків у цілі числа."""
        test_env = {"ACCESS_TOKEN_EXPIRE_MINUTES": "60", "MAX_FILE_SIZE": "1048576"}

        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()
            # Перевіримо що значення конвертуються правильно
            assert isinstance(settings.max_file_size, int)
            assert settings.max_file_size == 1048576
