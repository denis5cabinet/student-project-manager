"""
Базовое Flask-приложение для системы управления учебными проектами.
Автор: Гурьянов Денис (модуль комментариев)
"""
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Инициализация приложения
app = Flask(__name__)

# Конфигурация базы данных (SQLite для разработки)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JSON_AS_ASCII"] = False  # для корректного отображения русских символов

# Инициализация расширений
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# Пример простой модели (временная, позже заменим на свой модуль)
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)


# Корневой маршрут для проверки работоспособности
@app.route("/")
def index():
    return jsonify(
        {
            "status": "ok",
            "message": "Система управления учебными проектами",
            "version": "1.0",
        }
    )


# Пример защищённого маршрута (заглушка для будущей аутентификации)
@app.route("/api/health")
def health():
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
