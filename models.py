"""
Модели данных для модуля комментариев.
"""
from datetime import datetime, timezone
from extensions import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    comments = db.relationship('Comment', back_populates='author', lazy='dynamic')

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(50), default='new')
    deadline = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    comments = db.relationship('Comment', back_populates='task', lazy='dynamic')
    author = db.relationship('User', backref='tasks')

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_deleted = db.Column(db.Boolean, default=False)

    author = db.relationship('User', back_populates='comments')
    task = db.relationship('Task', back_populates='comments')
    parent_comment = db.relationship('Comment', remote_side=[id], backref='replies')

    __table_args__ = (
        db.Index('idx_comments_task_id', 'task_id'),
        db.Index('idx_comments_author_id', 'author_id'),
        db.Index('idx_comments_parent_id', 'parent_comment_id'),
        db.Index('idx_comments_created_at', 'created_at'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'author_id': self.author_id,
            'task_id': self.task_id,
            'parent_comment_id': self.parent_comment_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_deleted': self.is_deleted
        }