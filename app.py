"""
Базовое Flask-приложение с веб-интерфейсом и API для комментариев.
Автор: Гурьянов Денис
"""
import logging
from logging.handlers import RotatingFileHandler
import os
from flask import Flask, jsonify, render_template
from flask_migrate import Migrate
from models import db
from api import comments_bp

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False

db.init_app(app)
migrate = Migrate(app, db)

app.register_blueprint(comments_bp)


# Настройка логирования
def setup_logging():
    if not app.debug:
        # Создаём папку logs, если её нет
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/comments.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Application startup')


setup_logging()


@app.route('/')
def index():
    return jsonify({
        'status': 'ok',
        'message': 'Система управления учебными проектами',
        'version': '1.0'
    })


@app.route('/comments')
def comments_page():
    return render_template('comments.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)