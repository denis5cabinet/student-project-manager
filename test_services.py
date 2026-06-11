"""
Тестирование сервисного слоя модуля комментариев.
Запуск: python test_services.py
"""
import sys
from datetime import datetime, timedelta
from app import app
from models import db, User, Task
from services import create_comment_with_notification, update_comment_with_time_limit
from crud import get_comment


def setup_test_data():
    with app.app_context():
        db.drop_all()
        db.create_all()

        user1 = User(
            email="author@example.com", name="Автор Задачи", password_hash="hash1"
        )
        user2 = User(
            email="commenter@example.com", name="Комментатор", password_hash="hash2"
        )
        db.session.add_all([user1, user2])
        db.session.commit()

        task = Task(
            title="Тестовая задача",
            description="Для проверки комментариев",
            author_id=user1.id,
            status="new",
        )
        db.session.add(task)
        db.session.commit()
        return user1.id, user2.id, task.id


def test_comment_on_closed_task():
    print("\n=== Тест 1: Комментарий к закрытой задаче ===")
    with app.app_context():
        user1_id, user2_id, task_id = setup_test_data()
        task = Task.query.get(task_id)
        task.status = "closed"
        db.session.commit()

        try:
            create_comment_with_notification(
                content="Этот комментарий не должен создаться",
                author_id=user2_id,
                task_id=task_id,
            )
            print("❌ Ошибка: комментарий создался, хотя задача закрыта")
            sys.exit(1)
        except PermissionError as e:
            print(f"✅ Ожидаемая ошибка: {e}")


def test_comment_notification():
    print("\n=== Тест 2: Уведомление автору задачи ===")
    with app.app_context():
        user1_id, user2_id, task_id = setup_test_data()
        comment = create_comment_with_notification(
            content="Тестовый комментарий с уведомлением",
            author_id=user2_id,
            task_id=task_id,
        )
        print(f"✅ Комментарий создан (id={comment.id})")
        task = Task.query.get(task_id)
        assert task.author_id != comment.author_id
        print("✅ Уведомление отправлено (см. вывод выше)")


def test_edit_time_limit():
    print("\n=== Тест 3: Редактирование после истечения времени ===")
    with app.app_context():
        user1_id, user2_id, task_id = setup_test_data()
        comment = create_comment_with_notification(
            content="Оригинальный текст", author_id=user2_id, task_id=task_id
        )
        comment.created_at = datetime.utcnow() - timedelta(minutes=15)
        db.session.commit()

        try:
            update_comment_with_time_limit(
                comment_id=comment.id,
                new_content="Попытка редактирования",
                user_id=user2_id,
            )
            print("❌ Ошибка: редактирование разрешено, хотя прошло >10 минут")
            sys.exit(1)
        except PermissionError as e:
            print(f"✅ Ожидаемая ошибка: {e}")

        comment_refresh = get_comment(comment.id)
        assert comment_refresh.content == "Оригинальный текст"
        print("✅ Комментарий не изменился, ограничение сработало")


def test_edit_within_time():
    print("\n=== Тест 4: Редактирование в течение 10 минут ===")
    with app.app_context():
        user1_id, user2_id, task_id = setup_test_data()
        comment = create_comment_with_notification(
            content="Старый текст", author_id=user2_id, task_id=task_id
        )
        updated = update_comment_with_time_limit(
            comment_id=comment.id, new_content="Новый текст (вовремя)", user_id=user2_id
        )
        assert updated.content == "Новый текст (вовремя)"
        print("✅ Редактирование успешно выполнено")


if __name__ == "__main__":
    test_comment_on_closed_task()
    test_comment_notification()
    test_edit_time_limit()
    test_edit_within_time()
    print("\n=== Все тесты бизнес-логики пройдены ===")
