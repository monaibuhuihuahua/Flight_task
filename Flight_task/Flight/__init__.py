from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = 'my_secret_key_here'
    db.init_app(app)
    migrate.init_app(app, db)
    from . import models
    from .routes import main_bp
    app.register_blueprint(main_bp)
    return app