"""
Простий конфіг для unit тестів без складних фікстур.
"""

import pytest
import sys
import os

# Додамо src до PATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


# Базовий тест конфіг без бази даних
@pytest.fixture
def app_config():
    """Простий конфіг додатку для тестів."""
    return {
        "SECRET_KEY": "test-secret-key",
        "DATABASE_URL": "sqlite:///:memory:",
        "DEBUG": True,
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
    }
