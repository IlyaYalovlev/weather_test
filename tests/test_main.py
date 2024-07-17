import sys
import os

# Добавляем корневой каталог проекта в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import get_db
from main import app
from models import Base, User

# Создание тестовой базы данных
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


# Переопределение зависимостей для использования тестовой базы данных
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="module")
def session_id():
    return "test-session-id"


@pytest.fixture(scope="module")
def new_session_id():
    return "new-test-session-id"


def test_create_user(session_id):
    response = client.get("/", headers={"Session_id": session_id})
    assert response.status_code == 200
    db = next(override_get_db())
    user = db.query(User).filter(User.session_id == session_id).first()
    print(f"User found: {user}")
    assert user is not None


def test_get_weather(session_id):
    response = client.get("/weather?city=Moscow", headers={"Session_id": session_id})
    assert response.status_code == 200
    data = response.json()
    assert "current" in data
    assert "forecast" in data


def test_get_autocomplete(session_id):
    response = client.get("/autocomplete?query=Mos", headers={"Session_id": session_id})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_history(session_id):
    # Делаем запрос для создания истории
    client.get("/weather?city=Moscow", headers={"Session_id": session_id})
    client.get("/weather?city=Saint Petersburg", headers={"Session_id": session_id})

    # Проверяем историю запросов
    response = client.get("/history", headers={"Session_id": session_id})
    assert response.status_code == 200
    data = response.json()
    assert "history" in data
    assert "Moscow" in data["history"]
    assert "Saint Petersburg" in data["history"]


def test_create_user_if_not_found(new_session_id):
    response = client.get("/weather?city=Moscow", headers={"Session_id": new_session_id})
    assert response.status_code == 200
    db = next(override_get_db())
    user = db.query(User).filter(User.session_id == new_session_id).first()
    print(f"New user created: {user}")
    assert user is not None
