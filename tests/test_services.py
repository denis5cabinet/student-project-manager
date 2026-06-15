"""
Модульные тесты для бизнес-логики (services.py).
"""
import pytest
from datetime import datetime, timedelta
from models import db
from services import (
    create_comment_with_notification,
    update_comment_with_time_limit
)
from crud import get_comment


class TestServicesBusinessRules:

    def test_cant_comment_closed_task(self, app_context, test_task, test_users):
        """Нельзя комментировать закрытую задачу."""
        task = test_task
        task.status = 'closed'
        db.session.commit()   # сохраняем изменение
        with pytest.raises(PermissionError, match="закрытую задачу"):
            create_comment_with_notification(
                content="Попытка",
                author_id=test_users['commenter'].id,
                task_id=task.id
            )

    @pytest.mark.skip(reason="Требуется настройка логгера для проверки уведомлений")
    def test_notification_sent(self, app_context, test_task, test_users, capsys):
        """При создании комментария отправляется уведомление автору задачи."""
        create_comment_with_notification(
            content="Тест уведомления",
            author_id=test_users['commenter'].id,
            task_id=test_task.id
        )
        captured = capsys.readouterr()
        assert "УВЕДОМЛЕНИЕ" in captured.out

    def test_edit_within_time_limit(self, app_context, test_comment, test_users):
        """Редактирование в пределах 10 минут разрешено."""
        updated = update_comment_with_time_limit(
            comment_id=test_comment.id,
            new_content="Своевременная правка",
            user_id=test_users['commenter'].id
        )
        assert updated.content == "Своевременная правка"

    def test_edit_after_time_limit(self, app_context, test_comment, test_users):
        """Через 10 минут редактирование запрещено."""
        comment = get_comment(test_comment.id)
        comment.created_at = datetime.utcnow() - timedelta(minutes=15)
        db.session.commit()
        with pytest.raises(PermissionError, match="истекло время"):
            update_comment_with_time_limit(
                comment_id=test_comment.id,
                new_content="Поздняя правка",
                user_id=test_users['commenter'].id
            )