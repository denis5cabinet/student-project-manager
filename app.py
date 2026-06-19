from flask import Flask, jsonify, render_template
from flask_migrate import Migrate
from models import db
from api import comments_bp
from extensions import cache

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JSON_AS_ASCII"] = False

db.init_app(app)
migrate = Migrate(app, db)

# Инициализация кэша
cache.init_app(app, config={"CACHE_TYPE": "SimpleCache"})

app.register_blueprint(comments_bp)


@app.route("/")
def index():
    return jsonify({"status": "ok", "message": "Система управления учебными проектами"})


@app.route("/comments")
def comments_page():
    return render_template("comments.html")


if __name__ == "__main__":
    app.run(debug=True)
