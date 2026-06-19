"""
REST API для модуля комментариев.
"""
import logging
from flask import Blueprint, request, jsonify
from extensions import cache
from services import (
    create_comment_with_notification,
    update_comment_with_time_limit,
    delete_comment_with_checks,
    get_task_comments_safe
)
from crud import get_comment

logger = logging.getLogger(__name__)
comments_bp = Blueprint('comments', __name__, url_prefix='/api/comments')

def get_current_user():
    return 1

def is_admin():
    return False

@comments_bp.route('/', methods=['POST'])
def add_comment():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data'}), 400
    content = data.get('content')
    task_id = data.get('task_id')
    parent_id = data.get('parent_comment_id')
    if not content or not task_id:
        return jsonify({'error': 'Missing required fields'}), 400
    try:
        comment = create_comment_with_notification(
            content=content,
            author_id=get_current_user(),
            task_id=task_id,
            parent_comment_id=parent_id
        )
        return jsonify(comment.to_dict()), 201
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception:
        logger.exception("Unexpected error in add_comment")
        return jsonify({'error': 'Internal server error'}), 500

@comments_bp.route('/', methods=['GET'])
@cache.cached(timeout=30, query_string=True)
def list_comments():
    task_id = request.args.get('task_id', type=int)
    if not task_id:
        return jsonify({'error': 'task_id required'}), 400
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    try:
        comments, total = get_task_comments_safe(task_id, page, limit)
        return jsonify({
            'data': [c.to_dict() for c in comments],
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception:
        logger.exception("Error in list_comments")
        return jsonify({'error': 'Internal server error'}), 500

@comments_bp.route('/<int:comment_id>', methods=['GET'])
@cache.cached(timeout=30)
def get_comment_by_id(comment_id):
    try:
        comment = get_comment(comment_id)
        return jsonify(comment.to_dict()), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception:
        logger.exception("Error in get_comment_by_id")
        return jsonify({'error': 'Internal server error'}), 500

@comments_bp.route('/<int:comment_id>', methods=['PUT'])
def update_comment(comment_id):
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': 'Missing content'}), 400
    try:
        comment = update_comment_with_time_limit(
            comment_id=comment_id,
            new_content=data['content'],
            user_id=get_current_user(),
            is_admin=is_admin()
        )
        return jsonify(comment.to_dict()), 200
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception:
        logger.exception("Error in update_comment")
        return jsonify({'error': 'Internal server error'}), 500

@comments_bp.route('/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    try:
        delete_comment_with_checks(
            comment_id=comment_id,
            user_id=get_current_user(),
            is_admin=is_admin(),
            hard=False
        )
        return jsonify({'message': 'Deleted'}), 200
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception:
        logger.exception("Error in delete_comment")
        return jsonify({'error': 'Internal server error'}), 500