"""REST API для модуля комментариев.

Предоставляет эндпоинты для управления комментариями через HTTP.
Все запросы требуют JWT-аутентификации (в текущей версии – заглушка).
"""

import logging
from flask import Blueprint, request, jsonify
from services import (
    create_comment_with_notification,
    update_comment_with_time_limit,
    delete_comment_with_checks,
    get_task_comments_safe,
)
from crud import get_comment

logger = logging.getLogger(__name__)
comments_bp = Blueprint("comments", __name__, url_prefix="/api/comments")


def get_current_user():
    """Временно: возвращает ID текущего пользователя (заглушка).

    В реальном проекте здесь будет извлечение user_id из JWT-токена.

    Returns:
        int: ID пользователя (1 – Иван Петров).
    """
    return 1


def is_admin():
    """Заглушка для проверки прав администратора.

    Returns:
        bool: False (временно).
    """
    return False


@comments_bp.route("/", methods=["POST"])
def add_comment():
    """Добавляет новый комментарий.

    **Request body (JSON):**
        - content (str): Текст комментария (обязательно).
        - task_id (int): ID задачи (обязательно).
        - parent_comment_id (int, optional): ID родительского комментария.

    **Responses:**
        - 201: Комментарий создан, возвращает его JSON.
        - 400: Неверные данные.
        - 403: Попытка комментировать закрытую задачу.
        - 500: Внутренняя ошибка.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data"}), 400
    content = data.get("content")
    task_id = data.get("task_id")
    parent_id = data.get("parent_comment_id")
    if not content or not task_id:
        return jsonify({"error": "Missing required fields"}), 400
    try:
        comment = create_comment_with_notification(
            content=content,
            author_id=get_current_user(),
            task_id=task_id,
            parent_comment_id=parent_id,
        )
        return jsonify(comment.to_dict()), 201
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.exception("Unexpected error in add_comment")
        return jsonify({"error": "Internal server error"}), 500


@comments_bp.route("/", methods=["GET"])
def list_comments():
    """Возвращает список комментариев задачи с пагинацией.

    **Query parameters:**
        - task_id (int): ID задачи (обязательно).
        - page (int): Номер страницы (по умолчанию 1).
        - limit (int): Количество на странице (по умолчанию 20, макс 100).

    **Responses:**
        - 200: JSON с полями `data` и `pagination`.
        - 400: Отсутствует task_id.
        - 404: Задача не найдена.
    """
    task_id = request.args.get("task_id", type=int)
    if not task_id:
        return jsonify({"error": "task_id required"}), 400
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 20, type=int)
    try:
        comments, total = get_task_comments_safe(task_id, page, limit)
        return (
            jsonify(
                {
                    "data": [c.to_dict() for c in comments],
                    "pagination": {
                        "page": page,
                        "limit": limit,
                        "total": total,
                        "pages": (total + limit - 1) // limit,
                    },
                }
            ),
            200,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.exception("Error in list_comments")
        return jsonify({"error": "Internal server error"}), 500


@comments_bp.route("/<int:comment_id>", methods=["GET"])
def get_comment_by_id(comment_id):
    """Возвращает один комментарий по ID.

    **Responses:**
        - 200: JSON комментария.
        - 404: Комментарий не найден.
    """
    try:
        comment = get_comment(comment_id)
        return jsonify(comment.to_dict()), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.exception("Error in get_comment_by_id")
        return jsonify({"error": "Internal server error"}), 500


@comments_bp.route("/<int:comment_id>", methods=["PUT"])
def update_comment(comment_id):
    """Обновляет текст комментария.

    **Request body (JSON):**
        - content (str): Новый текст (обязательно).

    **Responses:**
        - 200: Обновлённый комментарий.
        - 400: Отсутствует content.
        - 403: Нет прав или истекло время редактирования.
        - 404: Комментарий не найден.
    """
    data = request.get_json()
    if not data or "content" not in data:
        return jsonify({"error": "Missing content"}), 400
    try:
        comment = update_comment_with_time_limit(
            comment_id=comment_id,
            new_content=data["content"],
            user_id=get_current_user(),
            is_admin=is_admin(),
        )
        return jsonify(comment.to_dict()), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.exception("Error in update_comment")
        return jsonify({"error": "Internal server error"}), 500


@comments_bp.route("/<int:comment_id>", methods=["DELETE"])
def delete_comment(comment_id):
    """Удаляет комментарий (мягкое удаление).

    **Responses:**
        - 200: {'message': 'Deleted'}.
        - 403: Нет прав.
        - 404: Комментарий не найден.
    """
    try:
        delete_comment_with_checks(
            comment_id=comment_id,
            user_id=get_current_user(),
            is_admin=is_admin(),
            hard=False,
        )
        return jsonify({"message": "Deleted"}), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.exception("Error in delete_comment")
        return jsonify({"error": "Internal server error"}), 500
