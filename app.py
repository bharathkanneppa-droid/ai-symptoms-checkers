"""MediAssist AI - application factory and entry point.

Run locally with:

    pip install -r requirements.txt
    python app.py

For production (Render/Railway/PythonAnywhere) import ``app`` from this module
or from ``wsgi`` - see README.
"""
import os
from datetime import datetime
from utils.time import utcnow

from flask import Flask, render_template
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_wtf import CSRFProtect

from config import Config
from database.db import db
from database.seed import seed_if_empty
from models import User
from routes import register_blueprints

bcrypt = Bcrypt()
login_manager = LoginManager()
csrf = CSRFProtect()


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Extensions
    db.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to continue."
    login_manager.login_message_category = "warning"

    # Blueprints
    register_blueprints(app)

    # Templates helpers
    @app.context_processor
    def inject_globals():
        from flask_login import current_user as cu
        from models import Notification

        unread_count = 0
        recent_notifications = []
        if cu.is_authenticated:
            recent_notifications = (
                Notification.query.filter_by(user_id=cu.id)
                .order_by(Notification.created_at.desc())
                .limit(6)
                .all()
            )
            unread_count = Notification.query.filter_by(
                user_id=cu.id, is_read=False
            ).count()
        return {
            "app_name": app.config["APP_NAME"],
            "unread_count": unread_count,
            "recent_notifications": recent_notifications,
            "current_year": utcnow().year,
        }

    # Error pages
    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def server_error(error):
        return render_template("errors/500.html"), 500

    # Create tables and seed demo data on first run.
    with app.app_context():
        seed_if_empty()

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true")
