import os

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from app.config import DevelopmentConfig, ProductionConfig, TestingConfig


def _resolve_config_class():
    app_env = os.getenv("APP_ENV", "development").lower()
    mapping = {
        "development": DevelopmentConfig,
        "testing": TestingConfig,
        "production": ProductionConfig,
    }
    return mapping.get(app_env, DevelopmentConfig)

app = Flask(__name__, instance_relative_config=True)
app.config.from_object(_resolve_config_class())
os.makedirs(app.instance_path, exist_ok=True)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)  # object to hash the password
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)
login_manager = LoginManager(app)  # validation during log in
login_manager.login_view = "auth.welcome"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"
mail = Mail(app)
migrate = Migrate(app, db)


@login_manager.user_loader
def load_user(user_id):
    from app.model import Todoers

    return Todoers.query.get(int(user_id))


@app.context_processor
def inject_runtime_config():
    weather_key = app.config.get("WEATHER_WIDGET_KEY", "")
    return {
        "weather_widget_enabled": bool(weather_key),
        "weather_widget_key": weather_key,
    }


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    response.headers[
        "Content-Security-Policy"
    ] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://widget.qweather.net; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "frame-src 'self'"
    )
    if request.is_secure:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


from app.routes import auth_bp, task_bp, chart_bp

app.register_blueprint(auth_bp)
app.register_blueprint(task_bp)
app.register_blueprint(chart_bp)
