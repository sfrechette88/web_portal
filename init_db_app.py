#!/usr/bin/env python3
from app import create_app, db
from app.models.user import User
from werkzeug.security import generate_password_hash

app = create_app()  # Utilise toute la config (et donc le .env !)

with app.app_context():
    # Crée toutes les tables selon les modèles existants
    db.drop_all()     # Optionnel : pour reset complet ! ATTENTION : tout sera effacé !
    db.create_all()
    print("Tables créées dans la base de données (config: %s)" % app.config['SQLALCHEMY_DATABASE_URI'])

    # Crée des utilisateurs de base (exemple)
    users = [
        dict(username='gestionnaire', email='gestionnaire@example.com', role='manager', first_name='Gestionnaire', last_name=''),
        dict(username='employe', email='employe@example.com', role='employee', first_name='Employé', last_name=''),
    ]
    for u in users:
        if not User.query.filter_by(username=u['username']).first():
            user = User(
                username=u['username'],
                email=u['email'],
                first_name=u['first_name'],
                last_name=u['last_name'],
                role=u['role']
            )
            user.password_hash = generate_password_hash('password')
            db.session.add(user)
            print(f"Utilisateur {u['username']} créé")
    db.session.commit()
    print("Base de données initialisée avec succès !")
