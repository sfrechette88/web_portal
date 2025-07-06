#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# --- ajoute le dossier parent (timeportal/) au PYTHONPATH ---
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

# Charger .env avant tout (pour SECRET_KEY, DATABASE_URI…)
from dotenv import load_dotenv
load_dotenv(dotenv_path=root / '.env')

# Imports de votre application
from app import create_app, db
from app.models.user import User
from werkzeug.security import generate_password_hash


def main():
    """
    Crée quatre comptes par défaut :
      • employe / password / rôle = 'employee'
      • gestionnaire  / password / rôle = 'manager'
      • admin    / password / rôle = 'admin'
      • samuel   / password / rôle = 'admin'  # Compte admin additionnel
    """
    app = create_app()
    with app.app_context():
        comptes = [
            {'username': 'employe', 'email': 'employe@example.com', 'password': 'password', 'role': 'employee', 'first_name': 'Test', 'last_name': 'Employee'},
            {'username': 'gestionnaire',  'email': 'gestionnaire@example.com',  'password': 'password', 'role': 'manager', 'first_name': 'Admin', 'last_name': 'Manager'},
            {'username': 'admin',    'email': 'admin@example.com',    'password': 'password', 'role': 'admin', 'first_name': 'Super', 'last_name': 'Admin'},
            {'username': 'samuel',   'email': 'samuel@example.com',   'password': 'password', 'role': 'admin', 'first_name': 'Samuel', 'last_name': 'Fréchette'},
        ]

        for info in comptes:
            if User.query.filter_by(username=info['username']).first():
                print(f"🏷️ L'utilisateur '{info['username']}' existe déjà, on passe.")
                continue

            # Crée l'utilisateur
            u = User(
                username=info['username'],
                email=info['email'],
                role=info['role'],
                first_name=info['first_name'],
                last_name=info['last_name'],
            )
            # Hash du mot de passe en pbkdf2:sha256 pour rester sous 128 caractères
            u.password_hash = generate_password_hash(info['password'], method='pbkdf2:sha256')

            db.session.add(u)
            print(f"✅ Utilisateur '{info['username']}' ajouté.")

        db.session.commit()
        print("🎉 Seed terminé : 4 comptes créés.")

if __name__ == '__main__':
    main()
