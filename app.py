import os
from flask import Flask, jsonify, render_template
from extensions import db, migrate, cache
from api import comments_bp

app = Flask(__name__)

# Конфигурация базы данных из переменной окружения
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///project.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False

# Инициализация расширений
db.init_app(app)
migrate.init_app(app, db)
cache.init_app(app, config={'CACHE_TYPE': 'SimpleCache'})

app.register_blueprint(comments_bp)

@app.route('/')
def index():
    return jsonify({'status': 'ok', 'message': 'Система управления учебными проектами'})

@app.route('/comments')
def comments_page():
    return render_template('comments.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)