from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config
import locale
from babel.dates import format_date

db = SQLAlchemy()
migrate = Migrate()

def date_fr_court(value):
    if not value:
        return ''
    return format_date(value, format="d MMM yyyy", locale='fr_FR')

def jour_fr(value):
    if not value:
        return ''
    return format_date(value, format="EEEE", locale='fr_FR').capitalize()

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

    # 🔥 ENREGISTREMENT DU FILTRE ICI
    app.jinja_env.filters['date_fr_court'] = date_fr_court
    app.jinja_env.filters['jour_fr'] = jour_fr
    
    return app

from app.models.user import User
from app.models.timesheet import Timesheet
from app.models.audit_log import AuditLog