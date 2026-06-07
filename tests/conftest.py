"""
conftest.py — патчим движок SQLAlchemy ДО любых импортов из app.
Суть: session.py при импорте создаёт engine из settings.DATABASE_URL.
Мы подменяем весь модуль session целиком, подсовывая тестовый engine.
"""
import uuid
import sys
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

mock_settings = MagicMock()
mock_settings.APP_NAME = "task-service-test"
mock_settings.DATABASE_URL = "sqlite://"          # shared in-memory
mock_settings.AMQP_URL = "amqp://guest:guest@localhost/"
mock_settings.TASK_QUEUE_NAME = "tasks"
mock_settings.TASK_QUEUE_MAX_PRIORITY = 10
mock_settings.MAX_CONCURRENT_PROCESSES = 1
mock_settings.TIME_TO_WAIT_TASK = 10
sys.modules["app.packages.configs"] = MagicMock(settings=mock_settings)

# тестовый движок (shared in-memory — одна БД на весь процесс)
TEST_ENGINE = create_engine(
    "sqlite:///./test.db",
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(
    bind=TEST_ENGINE, autoflush=False, autocommit=False, expire_on_commit=False
)

# Патчим app.packages.db.session ДО импорта любого модуля приложения
fake_session_module = MagicMock()
fake_session_module.engine = TEST_ENGINE
fake_session_module.SessionLocal = TestingSessionLocal
sys.modules["app.packages.db.session"] = fake_session_module

from app.packages.db.base import Base
from app.packages.db.models import Task
from app.packages.enums import TaskPriority, TaskStatus


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Создаём таблицы один раз на всю сессию тестов."""
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture(scope="function")
def db(create_tables):
    """Каждый тест получает чистую транзакцию, которая откатывается после."""
    connection = TEST_ENGINE.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def sample_task(db):
    task = Task(
        id=uuid.uuid4(),
        title="Test Task",
        description="Test description",
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.NEW,
        created_at=datetime.now(timezone.utc),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@pytest.fixture
def mock_publisher():
    with patch("app.services.task_service.TaskPublisher") as mock_cls:
        instance = AsyncMock()
        instance.publish_task = AsyncMock()
        mock_cls.return_value = instance
        yield instance


@pytest.fixture
def client(db, mock_publisher):
    from app.packages.db.dependencies import get_db
    from main import app

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
