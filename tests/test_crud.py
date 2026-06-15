"""
Модульные тесты для CRUD-функций (crud.py).
"""
import pytest
from crud import (
    validate_comment_content,
    create_comment,
    get_comment,
    update_comment,
    delete_comment,
    get_comments_by_task
)
from models import Comment


class TestValidation:
    """Тесты валидации комментариев."""

    def test_validate_empty_content(self):
        """Пустой комментарий -> ValueError."""
        with pytest.raises(ValueError, match="не может быть пустым"):
            validate_comment_content("")

    def test_validate_whitespace_content(self):
        """Комментарий из пробелов -> ValueError."""
        with pytest.raises(ValueError, match="не может быть пустым"):
            validate_comment_content("   ")

    def test_validate_too_long_content(self):
        """Слишком длинный комментарий (>2000) -> ValueError."""
        long_text = "A" * 2001
        with pytest.raises(ValueError, match="не может превышать 2000"):
            validate_comment_content(long_text)

    def test_validate_valid_content(self):
        """Корректный комментарий -> возвращает очищенную строку."""
        result = validate_comment_content("  Привет!  ")
        assert result == "Привет!"


class TestCRUDCreate:
    """Тесты создания комментариев."""

    def test_create_comment_success(self, app_context, test_task, test_users):
        """Успешное создание комментария."""
        comment = create_comment(
            content="Новый комментарий",
            author_id=test_users['commenter'].id,
            task_id=test_task.id
        )
        assert comment.id is not None
        assert comment.content == "Новый комментарий"
        assert comment.author_id == test_users['commenter'].id

    def test_create_comment_invalid_task(self, app_context, test_users):
        """Несуществующая задача -> ValueError."""
        with pytest.raises(ValueError, match="не существует"):
            create_comment("Текст", test_users['commenter'].id, task_id=99999)

    def test_create_comment_with_parent(self, app_context, test_task, test_users, test_comment):
        """Создание ответа на существующий комментарий."""
        reply = create_comment(
            content="Ответ",
            author_id=test_users['commenter'].id,
            task_id=test_task.id,
            parent_comment_id=test_comment.id
        )
        assert reply.parent_comment_id == test_comment.id


class TestCRUDRead:
    """Тесты чтения комментариев."""

    def test_get_comment_success(self, app_context, test_comment):
        """Получение существующего комментария."""
        comment = get_comment(test_comment.id)
        assert comment.id == test_comment.id

    def test_get_comment_not_found(self, app_context):
        """Несуществующий ID -> ValueError."""
        with pytest.raises(ValueError, match="не найден"):
            get_comment(99999)

    def test_get_comments_by_task(self, app_context, test_task, test_comment):
        """Получение списка комментариев задачи."""
        comments, total = get_comments_by_task(test_task.id)
        assert total >= 1
        assert any(c.id == test_comment.id for c in comments)


class TestCRUDUpdate:
    """Тесты обновления комментариев."""

    def test_update_comment_as_author(self, app_context, test_comment, test_users):
        """Автор может обновить свой комментарий."""
        updated = update_comment(
            comment_id=test_comment.id,
            new_content="Обновлённый текст",
            user_id=test_users['commenter'].id,
            is_admin=False
        )
        assert updated.content == "Обновлённый текст"

    def test_update_comment_as_admin(self, app_context, test_comment, test_users):
        """Администратор может обновить чужой комментарий."""
        updated = update_comment(
            comment_id=test_comment.id,
            new_content="Админ отредактировал",
            user_id=test_users['author'].id,
            is_admin=True
        )
        assert updated.content == "Админ отредактировал"

    def test_update_comment_as_other_user(self, app_context, test_comment, test_users):
        """Обычный пользователь не может редактировать чужой комментарий."""
        with pytest.raises(PermissionError, match="нет прав"):
            update_comment(
                comment_id=test_comment.id,
                new_content="Чужая правка",
                user_id=test_users['author'].id,  # автор задачи, но не комментария
                is_admin=False
            )


class TestCRUDDelete:
    """Тесты удаления комментариев."""

    def test_soft_delete(self, app_context, test_comment, test_users):
        """Мягкое удаление: is_deleted=True, контент заменяется."""
        delete_comment(test_comment.id, user_id=test_users['commenter'].id, hard=False)
        deleted = get_comment(test_comment.id)
        assert deleted.is_deleted is True
        assert deleted.content == "[Комментарий удалён]"

    def test_hard_delete(self, app_context, test_comment, test_users):
        """Жёсткое удаление: запись исчезает из БД."""
        delete_comment(test_comment.id, user_id=test_users['commenter'].id, hard=True)
        with pytest.raises(ValueError):
            get_comment(test_comment.id)