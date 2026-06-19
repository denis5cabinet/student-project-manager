"""
Интеграционные тесты для модуля комментариев.
"""
import pytest
from app import app
from extensions import db
from models import User, Task, Comment


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            user = User(email="test@test.com", name="Test User", password_hash="hash")
            db.session.add(user)
            db.session.commit()
            task = Task(
                title="Test Task", description="Desc", author_id=user.id, status="new"
            )
            db.session.add(task)
            db.session.commit()
            client.test_user_id = user.id
            client.test_task_id = task.id
        yield client
        with app.app_context():
            db.drop_all()


def test_create_comment_integration(client):
    task_id = client.test_task_id
    response = client.post(
        "/api/comments/", json={"content": "Интеграционный тест", "task_id": task_id}
    )
    assert response.status_code == 201
    data = response.get_json()
    assert "id" in data
    assert data["content"] == "Интеграционный тест"


def test_comment_closed_task(client):
    with app.app_context():
        task = db.session.get(Task, client.test_task_id)
        task.status = "closed"
        db.session.commit()
    response = client.post(
        "/api/comments/", json={"content": "Попытка", "task_id": client.test_task_id}
    )
    assert response.status_code == 403
    assert "закрытую задачу" in response.get_json()["error"]


def test_update_own_comment(client):
    task_id = client.test_task_id
    resp = client.post(
        "/api/comments/", json={"content": "Оригинал", "task_id": task_id}
    )
    comment_id = resp.get_json()["id"]
    resp2 = client.put(
        f"/api/comments/{comment_id}", json={"content": "Обновлённый текст"}
    )
    assert resp2.status_code == 200
    assert resp2.get_json()["content"] == "Обновлённый текст"
