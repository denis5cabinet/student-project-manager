"""
REST API для модуля комментариев.
Эндпоинты используют сервисный слой (services.py).
Автор: Гурьянов Денис
"""
from flask import Blueprint, request, jsonify
from services import (
    create_comment_with_notification,
    update_comment_with_time_limit,
    delete_comment_with_checks,
    get_task_comments_safe
)
from crud import get_comment

comments_bp = Blueprint('comments', __name__, url_prefix='/api/comments')


def get_current_user():
    """Временно: имитация получения текущего пользователя из JWT."""
    # TODO: заменить на реальную аутентификацию
    return 1  # id пользователя (Иван Петров)


def is_admin():
    """Заглушка: проверка, является ли пользователь администратором."""
    return False


def serialize_comment(comment):
    """Превращает ORM-объект Comment в JSON-словарь."""
    return {
        'id': comment.id,
        'content': comment.content,
        'author_id': comment.author_id,
        'task_id': comment.task_id,
        'parent_comment_id': comment.parent_comment_id,
        'created_at': comment.created_at.isoformat() if comment.created_at else None,
        'updated_at': comment.updated_at.isoformat() if comment.updated_at else None,
        'is_deleted': comment.is_deleted
    }


@comments_bp.route('/', methods=['POST'])
def add_comment():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data'}), 400

    content = data.get('content')
    task_id = data.get('task_id')
    parent_id = data.get('parent_comment_id')

    if not content or not task_id:
        return jsonify({'error': 'Missing required fields: content, task_id'}), 400

    current_user_id = get_current_user()

    try:
        comment = create_comment_with_notification(
            content=content,
            author_id=current_user_id,
            task_id=task_id,
            parent_comment_id=parent_id
        )
        return jsonify(serialize_comment(comment)), 201
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@comments_bp.route('/', methods=['GET'])
def list_comments():
    task_id = request.args.get('task_id', type=int)
    if not task_id:
        return jsonify({'error': 'task_id parameter is required'}), 400

    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)

    try:
        comments, total = get_task_comments_safe(task_id, page=page, per_page=limit)
        comments_json = [serialize_comment(c) for c in comments]
        return jsonify({
            'data': comments_json,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@comments_bp.route('/<int:comment_id>', methods=['GET'])
def get_comment_by_id(comment_id):
    try:
        comment = get_comment(comment_id)
        return jsonify(serialize_comment(comment)), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@comments_bp.route('/<int:comment_id>', methods=['PUT'])
def update_comment(comment_id):
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': 'Missing content field'}), 400

    new_content = data['content']
    current_user_id = get_current_user()
    admin_flag = is_admin()

    try:
        updated_comment = update_comment_with_time_limit(
            comment_id=comment_id,
            new_content=new_content,
            user_id=current_user_id,
            is_admin=admin_flag
        )
        return jsonify(serialize_comment(updated_comment)), 200
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@comments_bp.route('/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    current_user_id = get_current_user()
    admin_flag = is_admin()
    try:
        delete_comment_with_checks(
            comment_id=comment_id,
            user_id=current_user_id,
            is_admin=admin_flag,
            hard=False
        )
        return jsonify({'message': 'Comment deleted successfully'}), 200
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500