from pathlib import Path

from flask import Flask

from .database import init_db
from .routes import main_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-secret-key"
    app.config["DATABASE"] = str(Path(app.root_path).parent / "attendance.db")

    init_db(app)
    app.register_blueprint(main_bp)
    return app
