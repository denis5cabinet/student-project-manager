"""
Модели данных для модуля комментариев.
Автор: Гурьянов Денис
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """Модель пользователя (ссылка на модуль аутентификации)."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связь с комментариями
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связь с комментариями
    comments = db.relationship("Comment", back_populates="task", lazy="dynamic")
    author = db.relationship("User", backref="tasks")

    def __repr__(self):
        return f"<Task {self.title}>"


class Comment(db.Model):
    """
    Модель комментария к задаче.
    Поддерживает вложенные ответы (self-referential relationship).
    """

    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    parent_comment_id = db.Column(
        db.Integer, db.ForeignKey("comments.id"), nullable=True
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    is_deleted = db.Column(db.Boolean, default=False)

    # Связи
    author = db.relationship("User", back_populates="comments")
    task = db.relationship("Task", back_populates="comments")
    parent_comment = db.relationship("Comment", remote_side=[id], backref="replies")

    # Индексы
    __table_args__ = (
        db.Index("idx_comments_task_id", "task_id"),
        db.Index("idx_comments_author_id", "author_id"),
        db.Index("idx_comments_parent_id", "parent_comment_id"),
        db.Index("idx_comments_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<Comment {self.id} by {self.author_id}>"


class ValidationMixin:
    """Миксин для валидации модели Comment."""

    @db.validates("content")
    def validate_content(self, key, content):
        if not content or not content.strip():
            raise ValueError("Комментарий не может быть пустым")
        if len(content) > 2000:
            raise ValueError("Комментарий не может превышать 2000 символов")
        return content.strip()
