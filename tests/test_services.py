"""
Модульные тесты для бизнес-логики (services.py).
"""
import pytest
import logging
from datetime import datetime, timezone, timedelta
from models import db
from extensions import db
from services import create_comment_with_notification, update_comment_with_time_limit
from crud import get_comment


class TestServicesBusinessRules:
    def test_cant_comment_closed_task(self, app_context, test_task, test_users):
        task = test_task
        task.status = "closed"
        db.session.commit()
        with pytest.raises(PermissionError, match="закрытую задачу"):
            create_comment_with_notification(
                content="Попытка", author_id=test_users["commenter"].id, task_id=task.id
            )

    def test_notification_sent(self, app_context, test_task, test_users, caplog):
        """Проверяет, что уведомление логируется."""
        caplog.set_level(logging.INFO)
        create_comment_with_notification(
            content="Тест уведомления",
            author_id=test_users["commenter"].id,
            task_id=test_task.id,
        )
        assert any("NOTIFICATION" in rec.message for rec in caplog.records)

    def test_edit_within_time_limit(self, app_context, test_comment, test_users):
        updated = update_comment_with_time_limit(
            comment_id=test_comment.id,
            new_content="Своевременная правка",
            user_id=test_users["commenter"].id,
        )
        assert updated.content == "Своевременная правка"

    def test_edit_after_time_limit(self, app_context, test_comment, test_users):
        comment = get_comment(test_comment.id)
        comment.created_at = datetime.now(timezone.utc) - timedelta(minutes=15)
        db.session.commit()
        with pytest.raises(PermissionError, match="истекло время"):
            update_comment_with_time_limit(
                comment_id=test_comment.id,
                new_content="Поздняя правка",
                user_id=test_users["commenter"].id,
            )
