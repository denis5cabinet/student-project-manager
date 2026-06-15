"""Сервисный слой модуля комментариев.

Реализует бизнес-правила:
- Запрет комментирования закрытой задачи.
- Отправка уведомления автору задачи.
- Ограничение времени редактирования (10 минут).
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, List
from models import Comment, Task
from crud import (
    create_comment as crud_create_comment,
    get_comment,
    update_comment as crud_update_comment,
    delete_comment as crud_delete_comment,
    get_comments_by_task as crud_get_comments_by_task,
)
from config import EDIT_TIME_LIMIT_MINUTES

logger = logging.getLogger(__name__)


def _get_task_status(task_id: int) -> str:
    """Возвращает статус задачи по ID.

    Args:
        task_id: ID задачи.

    Returns:
        str: Статус задачи ('new', 'in_progress', 'closed' и т.д.).

    Raises:
        ValueError: Если задача не найдена.
    """
    task = Task.query.get(task_id)
    if not task:
        raise ValueError(f"Задача с ID {task_id} не найдена")
    return task.status


def _is_task_closed(task_id: int) -> bool:
    """Проверяет, закрыта ли задача.

    Args:
        task_id: ID задачи.

    Returns:
        bool: True если статус 'closed', 'завершена' или 'done'.
    """
    status = _get_task_status(task_id)
    return status.lower() in ("closed", "завершена", "done")


def _can_edit_comment(comment: Comment, user_id: int, is_admin: bool = False) -> bool:
    """Проверяет, может ли пользователь редактировать комментарий.

    Args:
        comment: Объект комментария.
        user_id: ID пользователя.
        is_admin: Флаг администратора.

    Returns:
        bool: True если разрешено (администратор или автор и не прошло 10 минут).
    """
    if is_admin:
        return True
    if comment.author_id != user_id:
        return False
    time_limit = comment.created_at + timedelta(minutes=EDIT_TIME_LIMIT_MINUTES)
    return datetime.now(timezone.utc) <= time_limit


def _send_notification(user_id: int, comment: Comment) -> None:
    """Отправляет уведомление автору задачи (заглушка).

    В реальной интеграции здесь будет вызов модуля уведомлений (Долгушев).

    Args:
        user_id: ID получателя (автор задачи).
        comment: Комментарий, который был добавлен.
    """
    task = Task.query.get(comment.task_id)
    logger.info(
        f"NOTIFICATION: To user {user_id} (task '{task.title}') "
        f"new comment from {comment.author_id}: {comment.content[:50]}"
    )


def create_comment_with_notification(
    content: str, author_id: int, task_id: int, parent_comment_id: Optional[int] = None
) -> Comment:
    """Создаёт комментарий с проверкой статуса задачи и отправкой уведомления.

    Args:
        content: Текст комментария.
        author_id: ID автора.
        task_id: ID задачи.
        parent_comment_id: ID родительского комментария (опционально).

    Returns:
        Comment: Созданный комментарий.

    Raises:
        PermissionError: Если задача закрыта.
    """
    logger.info(f"Service create_comment: task={task_id}, author={author_id}")
    if _is_task_closed(task_id):
        logger.warning(f"Attempt to comment closed task {task_id} by user {author_id}")
        raise PermissionError("Нельзя комментировать закрытую задачу")

    comment = crud_create_comment(content, author_id, task_id, parent_comment_id)

    task = Task.query.get(task_id)
    if task.author_id != author_id:
        _send_notification(task.author_id, comment)

    return comment


def update_comment_with_time_limit(
    comment_id: int, new_content: str, user_id: int, is_admin: bool = False
) -> Comment:
    """Обновляет комментарий с учётом временного ограничения (10 минут).

    Args:
        comment_id: ID комментария.
        new_content: Новый текст.
        user_id: ID пользователя.
        is_admin: Флаг администратора.

    Returns:
        Comment: Обновлённый комментарий.

    Raises:
        PermissionError: Если прошло больше 10 минут или недостаточно прав.
    """
    comment = get_comment(comment_id)
    if not _can_edit_comment(comment, user_id, is_admin):
        logger.warning(
            f"User {user_id} cannot edit comment {comment_id} (time or rights)"
        )
        raise PermissionError(
            "Редактирование комментария недоступно: истекло время (10 минут) "
            "или отсутствуют права."
        )
    return crud_update_comment(comment_id, new_content, user_id, is_admin)


def delete_comment_with_checks(
    comment_id: int, user_id: int, is_admin: bool = False, hard: bool = False
) -> bool:
    """Удаляет комментарий с проверкой прав.

    Args:
        comment_id: ID комментария.
        user_id: ID пользователя.
        is_admin: Флаг администратора.
        hard: Жёсткое удаление.

    Returns:
        bool: True при успехе.
    """
    return crud_delete_comment(comment_id, user_id, is_admin, hard)


def get_task_comments_safe(
    task_id: int, page: int = 1, per_page: int = 20, user_id: Optional[int] = None
) -> Tuple[List[Comment], int]:
    """Возвращает комментарии задачи (обёртка над CRUD).

    Args:
        task_id: ID задачи.
        page: Номер страницы.
        per_page: Количество на странице.
        user_id: Не используется, оставлен для совместимости.

    Returns:
        Tuple[List[Comment], int]: (список комментариев, общее количество).
    """
    return crud_get_comments_by_task(task_id, page, per_page)
