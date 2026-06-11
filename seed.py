"""
Заполнение базы данных тестовыми данными.
Запуск: python seed.py
"""
from app import app
from models import db, User, Task, Comment
from datetime import date


def seed():
    with app.app_context():
        # Очистка
        db.drop_all()
        db.create_all()

        # Пользователи
        user1 = User(
            email="ivan@example.com", name="Иван Петров", password_hash="hash_ivan"
        )
        user2 = User(
            email="maria@example.com", name="Мария Сидорова", password_hash="hash_maria"
        )
        db.session.add_all([user1, user2])
        db.session.commit()

        # Задачи
        task1 = Task(
            title="Разработать API комментариев",
            description="Создать эндпоинты и валидацию для модуля комментариев",
            author_id=user1.id,
            status="in_progress",
            deadline=date(2025, 4, 1),
        )
        task2 = Task(
            title="Написать тесты для модуля",
            description="Покрыть модуль комментариев тестами",
            author_id=user2.id,
            status="new",
            deadline=date(2025, 4, 5),
        )
        db.session.add_all([task1, task2])
        db.session.commit()

        # Комментарии
        comment1 = Comment(
            content="Отличная задача, приступаю!", author_id=user2.id, task_id=task1.id
        )
        comment2 = Comment(
            content="Уточните требования по валидации",
            author_id=user1.id,
            task_id=task1.id,
            parent_comment_id=comment1.id,
        )
        comment3 = Comment(
            content="Сделаю до пятницы", author_id=user2.id, task_id=task2.id
        )
        db.session.add_all([comment1, comment2, comment3])
        db.session.commit()

        print("✅ Тестовые данные успешно добавлены!")
        print(f"📊 Пользователей: {User.query.count()}")
        print(f"📊 Задач: {Task.query.count()}")
        print(f"📊 Комментариев: {Comment.query.count()}")


if __name__ == "__main__":
    seed()
