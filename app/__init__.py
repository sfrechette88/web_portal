from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config
import locale
from babel.dates import format_date
from datetime import datetime
from zoneinfo import ZoneInfo

db = SQLAlchemy()
migrate = Migrate()


def date_fr_court(value):
    if not value:
        return ""
    return format_date(value, format="d MMM yyyy", locale="fr_FR")


def jour_fr(value):
    if not value:
        return ""
    return format_date(value, format="EEEE", locale="fr_FR").capitalize()


def datetime_local(value):
    if not value:
        return ""
    # Convertit le temps UTC en fuseau horaire local (ex: Canada/Eastern)
    local_tz = ZoneInfo("America/Montreal")  # ou "America/Montreal" si plus précis
    local_dt = value.replace(tzinfo=ZoneInfo("UTC")).astimezone(local_tz)
    return local_dt.strftime("%d/%m/%Y %H:%M:%S")


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 🔍 DEBUG : voir la DB que Flask utilise
    print(">>> SQLALCHEMY_DATABASE_URI =", app.config["SQLALCHEMY_DATABASE_URI"])
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:///"):
        db_file = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
        from pathlib import Path

        db_path = Path(db_file)
        print(">>> Fichier DB vu par Flask :", db_path)
        print(">>> Fichier existe ? ", db_path.exists())

    db.init_app(app)
    migrate.init_app(app, db)

    from app.routes.auth import auth_bp
    from app.routes.employee import employee_bp
    from app.routes.manager import manager_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(manager_bp)
    app.register_blueprint(admin_bp)

    app.jinja_env.filters["date_fr_court"] = date_fr_court
    app.jinja_env.filters["jour_fr"] = jour_fr
    app.jinja_env.filters["datetime_local"] = datetime_local

    return app


from app.models.user import User
from app.models.timesheet import Timesheet
from app.models.audit_log import AuditLog
