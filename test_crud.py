"""
Простое тестирование CRUD-операций для модуля комментариев.
Запуск: python test_crud.py
"""
import sys
from app import app
from crud import (
    create_comment,
    get_comment,
    get_comments_by_task,
    update_comment,
    delete_comment,
)


def test_crud():
    with app.app_context():
        print("=== Тестирование CRUD комментариев ===\n")

        # 1. Создание
        print("1. Создание комментария...")
        try:
            comment = create_comment(
                content="Это тестовый комментарий", author_id=1, task_id=1
            )
            print(f"   ✅ Создан комментарий ID: {comment.id}")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            sys.exit(1)

        # 2. Чтение
        print("\n2. Получение комментария по ID...")
        try:
            fetched = get_comment(comment.id)
            print(f"   ✅ Комментарий: {fetched.content[:50]}")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

        # 3. Список комментариев задачи
        print("\n3. Список комментариев задачи (task_id=1):")
        try:
            comments, total = get_comments_by_task(1, page=1, per_page=10)
            print(f"   Всего корневых комментариев: {total}")
            for c in comments:
                print(f"   - {c.id}: {c.content[:40]}")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

        # 4. Обновление
        print("\n4. Обновление комментария...")
        try:
            updated = update_comment(
                comment.id, "Обновлённый текст комментария", user_id=1
            )
            print(f"   ✅ Обновлён: {updated.content}")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

        # 5. Мягкое удаление
        print("\n5. Мягкое удаление комментария...")
        try:
            delete_comment(comment.id, user_id=1, is_admin=False, hard=False)
            deleted_comment = get_comment(comment.id)
            print("   ✅ Комментарий помечен удалённым.")
            print(f"   Содержимое: {deleted_comment.content}")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

        print("\n=== Тестирование завершено ===")


if __name__ == "__main__":
    test_crud()
