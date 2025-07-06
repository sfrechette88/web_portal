from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    from app.routes.auth import auth_bp
    from app.routes.employee import employee_bp
    from app.routes.manager import manager_bp
    from app.routes.admin import admin_bp  # Nouvelle ligne
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(manager_bp)
    app.register_blueprint(admin_bp)  # Nouvelle ligne
    
    return app

from app.models.user import User
from app.models.timesheet import Timesheet
from app.models.audit_log import AuditLog