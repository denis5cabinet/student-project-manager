"""Модели данных для модуля комментариев.

Содержит классы User, Task, Comment для работы с БД через SQLAlchemy.
Определяет связи между таблицами, индексы и метод сериализации.
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """Модель пользователя (ссылка на модуль аутентификации)."""

    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    comments = db.relationship("Comment", back_populates="author", lazy="dynamic")

    def __repr__(self):
        return f"<User {self.email}>"


class Task(db.Model):
    """Модель задачи (ссылка на модуль задач)."""

    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(50), default="new")
    deadline = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    comments = db.relationship("Comment", back_populates="task", lazy="dynamic")
    author = db.relationship("User", backref="tasks")

    def __repr__(self):
        return f"<Task {self.title}>"


class Comment(db.Model):
    """Модель комментария к задаче.

    Поддерживает вложенные ответы через self-referential связь.
    Использует мягкое удаление (is_deleted).

    Attributes:
        id: Уникальный идентификатор.
        content: Текст комментария (не более 2000 символов).
        author_id: ID автора (внешний ключ на users.id).
        task_id: ID задачи (внешний ключ на tasks.id).
        parent_comment_id: ID родительского комментария (NULL для корневых).
        created_at: Дата и время создания (UTC).
        updated_at: Дата и время последнего обновления.
        is_deleted: Флаг мягкого удаления.
    """

    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    parent_comment_id = db.Column(
        db.Integer, db.ForeignKey("comments.id"), nullable=True
    )
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    is_deleted = db.Column(db.Boolean, default=False)

    # Relationships
    author = db.relationship("User", back_populates="comments")
    task = db.relationship("Task", back_populates="comments")
    parent_comment = db.relationship("Comment", remote_side=[id], backref="replies")

    # Индексы для оптимизации
    __table_args__ = (
        db.Index("idx_comments_task_id", "task_id"),
        db.Index("idx_comments_author_id", "author_id"),
        db.Index("idx_comments_parent_id", "parent_comment_id"),
        db.Index("idx_comments_created_at", "created_at"),
    )

    def to_dict(self):
        """Преобразует объект комментария в словарь для JSON-сериализации.

        Returns:
            dict: Словарь с полями id, content, author_id, task_id,
                  parent_comment_id, created_at, updated_at, is_deleted.
        """
        return {
            "id": self.id,
            "content": self.content,
            "author_id": self.author_id,
            "task_id": self.task_id,
            "parent_comment_id": self.parent_comment_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_deleted": self.is_deleted,
        }

    def __repr__(self):
        return f"<Comment {self.id} by {self.author_id}>"
