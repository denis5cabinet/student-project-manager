"""
Фикстуры для тестов модуля комментариев.
"""
import pytest
from app import app
from models import db, User, Task, Comment
from datetime import datetime, date


@pytest.fixture(scope='function')
def app_context():
    """Создаёт контекст приложения и очищает БД после теста."""
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def test_users(app_context):
    """Создаёт двух тестовых пользователей."""
    user1 = User(email='author@test.com', name='Автор', password_hash='hash1')
    user2 = User(email='commenter@test.com', name='Комментатор', password_hash='hash2')
    db.session.add_all([user1, user2])
    db.session.commit()
    return {'author': user1, 'commenter': user2}


@pytest.fixture
def test_task(test_users):
    """Создаёт тестовую задачу (не закрытую)."""
    task = Task(
        title='Тестовая задача',
        description='Описание',
        author_id=test_users['author'].id,
        status='new',
        deadline=date(2025, 12, 31)
    )
    db.session.add(task)
    db.session.commit()
    return task


@pytest.fixture
def test_comment(test_task, test_users):
    """Создаёт тестовый комментарий."""
    comment = Comment(
        content='Тестовый комментарий',
        author_id=test_users['commenter'].id,
        task_id=test_task.id,
        parent_comment_id=None,
        is_deleted=False
    )
    db.session.add(comment)
    db.session.commit()
    return comment