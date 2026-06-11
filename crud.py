"""
CRUD-операции для модели Comment.
Автор: Гурьянов Денис
"""
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from models import db, Comment, Task


def validate_comment_content(content: str) -> str:
    """Валидация содержимого комментария."""
    if not content or not content.strip():
        raise ValueError("Комментарий не может быть пустым")
    if len(content) > 2000:
        raise ValueError("Комментарий не может превышать 2000 символов")
    return content.strip()


def check_task_exists(task_id: int) -> bool:
    """Проверка существования задачи."""
    return db.session.query(Task.query.filter_by(id=task_id).exists()).scalar()


def check_parent_comment_exists(parent_id: int) -> bool:
    """Проверка существования родительского комментария."""
    return db.session.query(Comment.query.filter_by(id=parent_id).exists()).scalar()


def create_comment(
    content: str, author_id: int, task_id: int, parent_comment_id: Optional[int] = None
) -> Comment:
    """Создание нового комментария."""
    validated_content = validate_comment_content(content)

    if not check_task_exists(task_id):
        raise ValueError(f"Задача с ID {task_id} не существует")

    if parent_comment_id is not None:
        if not check_parent_comment_exists(parent_comment_id):
            raise ValueError(
                f"Родительский комментарий с ID {parent_comment_id} не существует"
            )

    comment = Comment(
        content=validated_content,
        author_id=author_id,
        task_id=task_id,
        parent_comment_id=parent_comment_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        is_deleted=False,
    )

    try:
        db.session.add(comment)
        db.session.commit()
        return comment
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RuntimeError(f"Ошибка базы данных при создании комментария: {str(e)}")


def get_comment(comment_id: int) -> Comment:
    """Получение комментария по ID."""
    comment = Comment.query.get(comment_id)
    if comment is None:
        raise ValueError(f"Комментарий с ID {comment_id} не найден")
    return comment


def get_comments_by_task(
    task_id: int, page: int = 1, per_page: int = 20, include_replies: bool = True
) -> Tuple[List[Comment], int]:
    """
    Получение комментариев задачи с пагинацией.
    Возвращает (список корневых комментариев, общее количество).
    """
    if not check_task_exists(task_id):
        raise ValueError(f"Задача с ID {task_id} не существует")

    query = Comment.query.filter_by(task_id=task_id, parent_comment_id=None)
    total = query.count()
    per_page = min(per_page, 100)
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
    """Обновление текста комментария (только автор или админ)."""
    comment = get_comment(comment_id)

    if not (is_admin or comment.author_id == user_id):
        raise PermissionError("У вас нет прав на редактирование этого комментария")

    validated_content = validate_comment_content(new_content)
    comment.content = validated_content
    comment.updated_at = datetime.utcnow()

    try:
        db.session.commit()
        return comment
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RuntimeError(f"Ошибка БД при обновлении комментария: {str(e)}")


def delete_comment(
    comment_id: int, user_id: int, is_admin: bool = False, hard: bool = False
) -> bool:
    """
    Удаление комментария (мягкое или жёсткое).
    Только автор или админ.
    """
    comment = get_comment(comment_id)

    if not (is_admin or comment.author_id == user_id):
        raise PermissionError("У вас нет прав на удаление этого комментария")

    try:
        if hard:
            db.session.delete(comment)
        else:
            comment.is_deleted = True
            comment.content = "[Комментарий удалён]"
            comment.updated_at = datetime.utcnow()
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RuntimeError(f"Ошибка БД при удалении комментария: {str(e)}")
