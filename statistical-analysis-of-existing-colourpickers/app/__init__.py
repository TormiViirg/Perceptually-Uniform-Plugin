import secrets
from pathlib import Path
from flask import Flask

from .config import CONFIG
from .utils import ensure_dirs
from .routes import bp as main_bp


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder = "templates",
        instance_relative_config = True,  
    )

    Path(app.instance_path).mkdir(
        parents = True, 
        exist_ok = True
    )

    app.secret_key = secrets.token_hex(16)
    app.config["MAX_CONTENT_LENGTH"] = CONFIG.max_upload_mb * 1024 * 1024

    ensure_dirs()
    app.register_blueprint(main_bp)

    app.config["TEMPLATES_AUTO_RELOAD"] = True  # remember to remove
    app.jinja_env.auto_reload = True

    return app
