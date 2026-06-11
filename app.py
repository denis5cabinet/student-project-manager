"""
Базовое Flask-приложение для системы управления учебными проектами.
Автор: Гурьянов Денис (модуль комментариев)
"""
from flask import Flask, jsonify
from flask_migrate import Migrate
from models import db
from api import comments_bp

app = Flask(__name__)

# Конфигурация
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JSON_AS_ASCII"] = False

# Инициализация расширений
db.init_app(app)
migrate = Migrate(app, db)

# Регистрация Blueprint модуля комментариев
app.register_blueprint(comments_bp)


# Корневой маршрут
@app.route("/")
def index():
    return jsonify(
        {
            "status": "ok",
            "message": "Система управления учебными проектами",
            "version": "1.0",
        }
    )


@app.route("/api/health")
def health():
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
