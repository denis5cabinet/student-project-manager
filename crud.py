"""CRUD операции для модели Comment.

Содержит низкоуровневые функции для работы с БД:
- создание, чтение, обновление, удаление комментариев
- валидация входных данных
- проверка существования связанных записей
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError
from models import db, Comment, Task
from config import MAX_COMMENT_LENGTH, MAX_PAGE_LIMIT, DEFAULT_PAGE_LIMIT

logger = logging.getLogger(__name__)


def validate_comment_content(content: str) -> str:
    """Проверяет корректность текста комментария.

    Args:
        content: Исходный текст.

    Returns:
        str: Очищенный текст (без лишних пробелов по краям).

    Raises:
        ValueError: Если текст пустой или превышает максимальную длину.
    """
    if not content or not content.strip():
        raise ValueError("Комментарий не может быть пустым")
    if len(content) > MAX_COMMENT_LENGTH:
        raise ValueError(
            f"Комментарий не может превышать {MAX_COMMENT_LENGTH} символов"
        )
    return content.strip()


def check_task_exists(task_id: int) -> bool:
    """Проверяет существование задачи в БД.

    Args:
        task_id: ID задачи.

    Returns:
        bool: True если задача существует, иначе False.
    """
    return db.session.query(Task.query.filter_by(id=task_id).exists()).scalar()


def check_parent_comment_exists(parent_id: int) -> bool:
    """Проверяет существование родительского комментария.

    Args:
        parent_id: ID комментария.

    Returns:
        bool: True если комментарий существует, иначе False.
    """
    return db.session.query(Comment.query.filter_by(id=parent_id).exists()).scalar()


def create_comment(
    content: str, author_id: int, task_id: int, parent_comment_id: Optional[int] = None
) -> Comment:
    """Создаёт новый комментарий в БД.

    Args:
        content: Текст комментария.
        author_id: ID автора.
        task_id: ID задачи.
        parent_comment_id: ID родительского комментария (опционально, для ответов).

    Returns:
        Comment: Созданный объект комментария.

    Raises:
        ValueError: Если задача или родительский комментарий не существуют,
                    либо контент не прошёл валидацию.
        RuntimeError: При ошибке базы данных.
    """
    logger.info(f"Creating comment: task_id={task_id}, author_id={author_id}")
    validated_content = validate_comment_content(content)

    if not check_task_exists(task_id):
        raise ValueError(f"Задача с ID {task_id} не существует")
    if parent_comment_id is not None and not check_parent_comment_exists(
        parent_comment_id
    ):
        raise ValueError(
            f"Родительский комментарий с ID {parent_comment_id} не существует"
        )

    comment = Comment(
        content=validated_content,
        author_id=author_id,
        task_id=task_id,
        parent_comment_id=parent_comment_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        is_deleted=False,
    )
    try:
        db.session.add(comment)
        db.session.commit()
        logger.info(f"Comment created with id={comment.id}")
        return comment
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Failed to create comment: {str(e)}")
        raise RuntimeError(f"Ошибка базы данных при создании комментария: {str(e)}")


def get_comment(comment_id: int) -> Comment:
    """Возвращает комментарий по ID.

    Args:
        comment_id: ID комментария.

    Returns:
        Comment: Объект комментария.

    Raises:
        ValueError: Если комментарий не найден.
    """
    comment = Comment.query.get(comment_id)
    if comment is None:
        raise ValueError(f"Комментарий с ID {comment_id} не найден")
    return comment


def get_comments_by_task(
    task_id: int,
    page: int = 1,
    per_page: int = DEFAULT_PAGE_LIMIT,
    include_replies: bool = True,
) -> Tuple[List[Comment], int]:
    """Возвращает список комментариев задачи с пагинацией.

    Args:
        task_id: ID задачи.
        page: Номер страницы (начиная с 1).
        per_page: Количество комментариев на странице (макс. 100).
        include_replies: Если True, подгружает ответы к каждому комментарию.

    Returns:
        Tuple[List[Comment], int]: (список корневых комментариев, общее количество).

    Raises:
        ValueError: Если задача не существует.
    """
    logger.info(
        f"Fetching comments for task_id={task_id}, page={page}, per_page={per_page}"
    )
    if not check_task_exists(task_id):
        raise ValueError(f"Задача с ID {task_id} не существует")

    query = Comment.query.filter_by(task_id=task_id, parent_comment_id=None)
    total = query.count()
    per_page = min(per_page, MAX_PAGE_LIMIT)
    comments = (
        query.order_by(Comment.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    if include_replies and comments:
        comment_ids = [c.id for c in comments]
        replies = Comment.query.filter(Comment.parent_comment_id.in_(comment_ids)).all()
        replies_by_parent = {}
        for reply in replies:
            replies_by_parent.setdefault(reply.parent_comment_id, []).append(reply)
        for comment in comments:
            comment.replies_list = replies_by_parent.get(comment.id, [])

    return comments, total


def update_comment(
    comment_id: int, new_content: str, user_id: int, is_admin: bool = False
) -> Comment:
    """Обновляет текст комментария.

    Args:
        comment_id: ID комментария.
        new_content: Новый текст.
        user_id: ID текущего пользователя.
        is_admin: Флаг администратора (разрешает редактирование чужих).

    Returns:
        Comment: Обновлённый комментарий.

    Raises:
        PermissionError: Если пользователь не автор и не администратор.
        ValueError: Если комментарий не найден или новый текст невалиден.
        RuntimeError: При ошибке базы данных.
    """
    logger.info(f"Updating comment {comment_id} by user {user_id}, admin={is_admin}")
    comment = get_comment(comment_id)
    if not (is_admin or comment.author_id == user_id):
        raise PermissionError("У вас нет прав на редактирование")

    validated_content = validate_comment_content(new_content)
    comment.content = validated_content
    comment.updated_at = datetime.now(timezone.utc)
    try:
        db.session.commit()
        logger.info(f"Comment {comment_id} updated")
        return comment
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Failed to update comment {comment_id}: {str(e)}")
        raise RuntimeError(f"Ошибка базы данных при обновлении комментария: {str(e)}")


def delete_comment(
    comment_id: int, user_id: int, is_admin: bool = False, hard: bool = False
) -> bool:
    """Удаляет комментарий (мягкое или жёсткое удаление).

    Args:
        comment_id: ID комментария.
        user_id: ID текущего пользователя.
        is_admin: Флаг администратора.
        hard: True – полное удаление из БД, False – мягкое (is_deleted=True).

    Returns:
        bool: True в случае успеха.

    Raises:
        PermissionError: Если пользователь не автор и не администратор.
        ValueError: Если комментарий не найден.
        RuntimeError: При ошибке базы данных.
    """
    logger.info(f"Deleting comment {comment_id} by user {user_id}, hard={hard}")
    comment = get_comment(comment_id)
    if not (is_admin or comment.author_id == user_id):
        raise PermissionError("У вас нет прав на удаление")

    try:
        if hard:
            db.session.delete(comment)
            logger.info(f"Comment {comment_id} hard deleted")
        else:
            comment.is_deleted = True
            comment.content = "[Комментарий удалён]"
            comment.updated_at = datetime.now(timezone.utc)
            logger.info(f"Comment {comment_id} soft deleted")
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Failed to delete comment {comment_id}: {str(e)}")
        raise RuntimeError(f"Ошибка базы данных при удалении комментария: {str(e)}")
