"""
Сервисный слой для модуля комментариев.
Автор: Гурьянов Денис
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from models import Comment, Task
from crud import (
    create_comment as crud_create_comment,
    get_comment,
    update_comment as crud_update_comment,
    delete_comment as crud_delete_comment,
    get_comments_by_task as crud_get_comments_by_task,
)


def _get_task_status(task_id: int) -> str:
    task = Task.query.get(task_id)
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
    time_limit = comment.created_at + timedelta(minutes=10)
    return datetime.utcnow() <= time_limit


def _send_notification(user_id: int, comment: Comment) -> None:
    task = Task.query.get(comment.task_id)
    print(
        f"[УВЕДОМЛЕНИЕ] Пользователю {user_id} (задача {task.title}): "
        f"Новый комментарий от {comment.author_id}: {comment.content[:50]}"
    )


def create_comment_with_notification(
    content: str, author_id: int, task_id: int, parent_comment_id: Optional[int] = None
) -> Comment:
    if _is_task_closed(task_id):
        raise PermissionError("Нельзя комментировать закрытую задачу")

    comment = crud_create_comment(
        content=content,
        author_id=author_id,
        task_id=task_id,
        parent_comment_id=parent_comment_id,
    )

    task = Task.query.get(task_id)
    if task.author_id != author_id:
        _send_notification(task.author_id, comment)

    return comment


def update_comment_with_time_limit(
    comment_id: int, new_content: str, user_id: int, is_admin: bool = False
) -> Comment:
    comment = get_comment(comment_id)

    if not _can_edit_comment(comment, user_id, is_admin):
        raise PermissionError(
            "Редактирование комментария недоступно: истекло время (10 минут) "
            "или отсутствуют права."
        )

    return crud_update_comment(
        comment_id=comment_id,
        new_content=new_content,
        user_id=user_id,
        is_admin=is_admin,
    )


def delete_comment_with_checks(
    comment_id: int, user_id: int, is_admin: bool = False, hard: bool = False
) -> bool:
    return crud_delete_comment(
        comment_id=comment_id, user_id=user_id, is_admin=is_admin, hard=hard
    )


def get_task_comments_safe(
    task_id: int, page: int = 1, per_page: int = 20, user_id: Optional[int] = None
) -> Tuple[List[Comment], int]:
    return crud_get_comments_by_task(task_id, page, per_page)
