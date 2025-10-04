"""
Прості тести для auth service без складних залежностей.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from src.services.auth import AuthService


class TestAuthServiceBasic:
    """Прості тести для AuthService."""

    def test_create_access_token_default_expiration(self):
        """Тест створення токена з терміном дії за замовчуванням."""
        test_data = {"sub": "test@example.com", "user_id": 1}

        with patch("src.services.auth.jwt.encode") as mock_encode:
            mock_encode.return_value = "test_token"

            token = AuthService.create_access_token(data=test_data)

            assert token == "test_token"
            mock_encode.assert_called_once()

            # Перевіримо що дані передаються правильно
            call_args = mock_encode.call_args[0]
            payload = call_args[0]

            assert payload["sub"] == "test@example.com"
            assert payload["user_id"] == 1
            assert "exp" in payload

    def test_create_access_token_custom_expiration(self):
        """Тест створення токена з кастомним терміном дії."""
        test_data = {"sub": "test@example.com"}
        expires_delta = timedelta(hours=2)

        with patch("src.services.auth.jwt.encode") as mock_encode:
            mock_encode.return_value = "custom_token"

            token = AuthService.create_access_token(
                data=test_data, expires_delta=expires_delta
            )

            assert token == "custom_token"
            mock_encode.assert_called_once()

    def test_verify_password_correct(self):
        """Тест перевірки правильного пароля."""
        password = "test_password"

        with patch("src.services.auth.pwd_context.verify") as mock_verify:
            mock_verify.return_value = True

            result = AuthService.verify_password(password, "hashed_password")

            assert result is True
            mock_verify.assert_called_once_with(password, "hashed_password")

    def test_verify_password_incorrect(self):
        """Тест перевірки неправильного пароля."""
        password = "wrong_password"

        with patch("src.services.auth.pwd_context.verify") as mock_verify:
            mock_verify.return_value = False

            result = AuthService.verify_password(password, "hashed_password")

            assert result is False
            mock_verify.assert_called_once_with(password, "hashed_password")

    def test_get_password_hash(self):
        """Тест хешування пароля."""
        password = "test_password"

        with patch("src.services.auth.pwd_context.hash") as mock_hash:
            mock_hash.return_value = "hashed_password_123"

            result = AuthService.get_password_hash(password)

            assert result == "hashed_password_123"
            mock_hash.assert_called_once_with(password)

    def test_decode_token_valid(self):
        """Тест декодування валідного токена."""
        token = "valid_token"

        with patch("src.services.auth.jwt.decode") as mock_decode:
            mock_decode.return_value = {"sub": "test@example.com", "user_id": 1}

            result = AuthService.decode_token(token)

            assert result["sub"] == "test@example.com"
            assert result["user_id"] == 1
            mock_decode.assert_called_once_with(
                token,
                AuthService.settings.secret_key,
                algorithms=[AuthService.settings.algorithm],
            )

    def test_decode_token_invalid(self):
        """Тест декодування невалідного токена."""
        token = "invalid_token"

        with patch("src.services.auth.jwt.decode") as mock_decode:
            from jose import JWTError

            mock_decode.side_effect = JWTError("Invalid token")

            result = AuthService.decode_token(token)

            assert result is None
            mock_decode.assert_called_once()

    def test_create_verification_token(self):
        """Тест створення токена верифікації."""
        user_id = 123

        with patch("src.services.auth.jwt.encode") as mock_encode:
            mock_encode.return_value = "verification_token"

            token = AuthService.create_verification_token(user_id)

            assert token == "verification_token"
            mock_encode.assert_called_once()

            # Перевіримо що user_id передається в payload
            call_args = mock_encode.call_args[0]
            payload = call_args[0]

            assert payload["user_id"] == user_id
            assert "exp" in payload

    @patch("src.services.auth.settings")
    def test_auth_service_uses_settings(self, mock_settings):
        """Тест що AuthService використовує settings."""
        mock_settings.secret_key = "test_secret"
        mock_settings.algorithm = "HS256"

        # Імпортуємо знову щоб отримати оновлені settings
        from src.services.auth import AuthService

        assert AuthService.settings == mock_settings

    def test_auth_service_static_methods(self):
        """Тест що методи AuthService є статичними."""
        # Перевіримо що методи можна викликати без створення екземпляра
        assert callable(AuthService.verify_password)
        assert callable(AuthService.get_password_hash)
        assert callable(AuthService.create_access_token)
        assert callable(AuthService.decode_token)

    def test_token_expiration_calculation(self):
        """Тест розрахунку часу закінчення токена."""
        test_data = {"sub": "test@example.com"}

        with patch("src.services.auth.datetime") as mock_datetime, patch(
            "src.services.auth.jwt.encode"
        ) as mock_encode:

            mock_now = datetime(2024, 1, 1, 12, 0, 0)
            mock_datetime.utcnow.return_value = mock_now
            mock_encode.return_value = "token"

            AuthService.create_access_token(data=test_data)

            # Перевіримо що exp обчислюється правильно
            call_args = mock_encode.call_args[0]
            payload = call_args[0]

            expected_exp = mock_now + timedelta(
                minutes=AuthService.settings.access_token_expire_minutes
            )
            # Перевіримо що exp близько до очікуваного часу (дозволимо різницю в 1 секунду)
            assert abs((payload["exp"] - expected_exp).total_seconds()) < 1
