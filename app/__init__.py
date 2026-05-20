import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from app.config import DevelopmentConfig

app = Flask(__name__, instance_relative_config=True)
app.config.from_object(DevelopmentConfig)
os.makedirs(app.instance_path, exist_ok=True)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)  # object to hash the password
login_manager = LoginManager(app)  # validation during log in
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


from app.routes import auth_bp, task_bp, chart_bp

app.register_blueprint(auth_bp)
app.register_blueprint(task_bp)
app.register_blueprint(chart_bp)
