"""
Сервисный слой модуля комментариев.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, List
from extensions import db
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
    task = db.session.get(Task, task_id)
    if not task:
        raise ValueError(f"Задача с ID {task_id} не найдена")
    return task.status


def _is_task_closed(task_id: int) -> bool:
    status = _get_task_status(task_id)
    return status.lower() in ("closed", "завершена", "done")


def _can_edit_comment(comment: Comment, user_id: int, is_admin: bool = False) -> bool:
    if is_admin:
        return True
    if comment.author_id != user_id:
        return False
    time_limit = comment.created_at + timedelta(minutes=EDIT_TIME_LIMIT_MINUTES)
    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
    return now_naive <= time_limit


# TODO: интеграция с модулем уведомлений (Долгушев) через API-вызов
def _send_notification(user_id: int, comment: Comment) -> None:
    task = db.session.get(Task, comment.task_id)
    logger.info(
        f"NOTIFICATION: To user {user_id} (task '{task.title}') "
        f"new comment from {comment.author_id}: {comment.content[:50]}"
    )


def create_comment_with_notification(
    content: str, author_id: int, task_id: int, parent_comment_id: Optional[int] = None
) -> Comment:
    if _is_task_closed(task_id):
        logger.warning(f"Attempt to comment closed task {task_id} by user {author_id}")
        raise PermissionError("Нельзя комментировать закрытую задачу")

    comment = crud_create_comment(content, author_id, task_id, parent_comment_id)

    task = db.session.get(Task, task_id)
    if task.author_id != author_id:
        _send_notification(task.author_id, comment)

    return comment


def update_comment_with_time_limit(
    comment_id: int, new_content: str, user_id: int, is_admin: bool = False
) -> Comment:
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
    return crud_delete_comment(comment_id, user_id, is_admin, hard)


def get_task_comments_safe(
    task_id: int, page: int = 1, per_page: int = 20, user_id: Optional[int] = None
) -> Tuple[List[Comment], int]:
    return crud_get_comments_by_task(task_id, page, per_page)
