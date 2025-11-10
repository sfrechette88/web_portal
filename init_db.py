from app import create_app, db
from app.models.user import User
from app.models.timesheet import Timesheet
from werkzeug.security import generate_password_hash
from pathlib import Path

app = create_app()

with app.app_context():
    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    db_path = None

    # On ne gère que le cas SQLite ici
    if uri.startswith("sqlite:///"):
        db_path = Path(uri.replace("sqlite:///", ""))
        if db_path.exists():
            db_path.unlink()
            print(f"Base de données existante supprimée: {db_path}")

    db.create_all()
    print("Tables créées")

    manager = User(
        username="gestionnaire",
        email="gestionnaire@example.com",
        first_name="Gestionnaire",
        last_name="",
        role="manager",
    )
    manager.password_hash = generate_password_hash("password")
    db.session.add(manager)

    employee = User(
        username="employe",
        email="employe@example.com",
        first_name="Employé",
        last_name="",
        role="employee",
    )
    employee.password_hash = generate_password_hash("password")
    db.session.add(employee)

    admin = User(
        username="admin",
        email="admin@example.com",
        first_name="Administrateur",
        last_name="",
        role="admin",
    )
    admin.password_hash = generate_password_hash("210688")
    db.session.add(admin)

    db.session.commit()
    print("Utilisateurs initiaux créés")
