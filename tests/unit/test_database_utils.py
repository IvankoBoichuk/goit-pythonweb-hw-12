"""
Прості тести для database utilities та helpers.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.db import get_db


class TestDatabaseUtils:
    """Тести для утиліт бази даних."""

    def test_get_db_generator(self):
        """Тест що get_db є генератором."""
        # Перевіримо що get_db є генераторною функцією
        import types

        assert isinstance(get_db(), types.GeneratorType)

    @patch("src.database.db.SessionLocal")
    def test_get_db_session_handling(self, mock_session_local):
        """Тест правильного керування сесією в get_db."""
        mock_session = Mock()
        mock_session_local.return_value = mock_session

        # Викликаємо get_db як генератор
        db_gen = get_db()

        # Отримаємо сесію
        session = next(db_gen)
        assert session == mock_session

        # Закриємо генератор (симулюємо завершення запиту)
        try:
            next(db_gen)
        except StopIteration:
            pass

        # Перевіримо що сесія закрилася
        mock_session.close.assert_called_once()

    @patch("src.database.db.SessionLocal")
    def test_get_db_exception_handling(self, mock_session_local):
        """Тест що сесія закривається навіть при винятку."""
        mock_session = Mock()
        mock_session_local.return_value = mock_session

        db_gen = get_db()
        session = next(db_gen)

        # Симулюємо виняток під час обробки
        try:
            db_gen.throw(Exception("Test exception"))
        except Exception:
            pass

        # Сесія все одно повинна закритися
        mock_session.close.assert_called_once()


class TestDatabaseConnection:
    """Тести для з'єднання з базою даних."""

    def test_engine_creation(self):
        """Тест створення engine."""
        from src.database.db import engine

        assert engine is not None
        assert hasattr(engine, "connect")

    def test_session_local_creation(self):
        """Тест створення SessionLocal."""
        from src.database.db import SessionLocal

        assert SessionLocal is not None
        assert hasattr(SessionLocal, "__call__")

    @patch("src.database.db.create_engine")
    def test_engine_configuration(self, mock_create_engine):
        """Тест конфігурації engine."""
        # Переімпортуємо модуль щоб викликати create_engine
        import importlib
        from src.database import db

        importlib.reload(db)

        # Перевіримо що create_engine викликається з правильними параметрами
        mock_create_engine.assert_called()
        call_args = mock_create_engine.call_args

        # Перевіримо що URL передається
        assert len(call_args[0]) > 0  # Позиційний аргумент (URL)

    def test_base_metadata(self):
        """Тест що Base має metadata."""
        from src.database.models import Base

        assert hasattr(Base, "metadata")
        assert hasattr(Base.metadata, "create_all")


class TestDatabaseModelsIntegration:
    """Прості тести інтеграції моделей з базою даних."""

    def test_user_model_table_name(self):
        """Тест назви таблиці для моделі User."""
        from src.database.models import User

        assert User.__tablename__ == "users"

    def test_contact_model_table_name(self):
        """Тест назви таблиці для моделі Contact."""
        from src.database.models import Contact

        assert Contact.__tablename__ == "contacts"

    def test_models_have_primary_keys(self):
        """Тест що моделі мають первинні ключі."""
        from src.database.models import User, Contact

        # Перевіримо що у моделей є атрибут id
        assert hasattr(User, "id")
        assert hasattr(Contact, "id")

    def test_foreign_key_relationship(self):
        """Тест зв'язку між моделями."""
        from src.database.models import Contact

        # Перевіримо що Contact має зв'язок з User
        assert hasattr(Contact, "user_id")
        assert hasattr(Contact, "owner")

    def test_user_contacts_relationship(self):
        """Тест зворотного зв'язку User -> Contacts."""
        from src.database.models import User

        # Перевіримо що User має зв'язок з контактами
        assert hasattr(User, "contacts")

    def test_models_inherit_from_base(self):
        """Тест що моделі наслідуються від Base."""
        from src.database.models import User, Contact, Base

        assert issubclass(User, Base)
        assert issubclass(Contact, Base)


class TestSQLAlchemyConfiguration:
    """Тести конфігурації SQLAlchemy."""

    def test_base_registry(self):
        """Тест реєстру Base."""
        from src.database.models import Base

        # Перевіримо що Base має registry
        assert hasattr(Base, "registry")

    def test_metadata_tables(self):
        """Тест що metadata містить таблиці після імпорту моделей."""
        from src.database.models import Base, User, Contact

        # Після імпорту моделей metadata повинна містити таблиці
        table_names = Base.metadata.tables.keys()
        assert len(table_names) >= 2  # Мінімум User та Contact

    def test_create_all_method_exists(self):
        """Тест що метод create_all існує."""
        from src.database.models import Base

        assert hasattr(Base.metadata, "create_all")
        assert callable(Base.metadata.create_all)

    def test_drop_all_method_exists(self):
        """Тест що метод drop_all існує."""
        from src.database.models import Base

        assert hasattr(Base.metadata, "drop_all")
        assert callable(Base.metadata.drop_all)
