from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
import os

# Configuration minimale pour créer la base de données
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///web_portal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Définir les modèles minimalement nécessaires
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    role = db.Column(db.String(20))  # 'employee' ou 'manager'
    
    # Relation avec les feuilles de temps (un utilisateur peut avoir plusieurs feuilles de temps)
    timesheets = db.relationship('Timesheet', backref='user', lazy='dynamic',
                                foreign_keys='Timesheet.user_id')
    
    # Relation pour les feuilles validées
    validated_timesheets = db.relationship('Timesheet', backref='validator', lazy='dynamic',
                                         foreign_keys='Timesheet.validator_id')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

class Timesheet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.Date, index=True)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    break_duration = db.Column(db.Integer, default=0)  # Durée de pause en minutes
    description = db.Column(db.String(200))
    status = db.Column(db.String(20), default='submitted')  # 'submitted', 'approved', 'rejected'
    
    # Validateur (manager qui a approuvé/rejeté la feuille de temps)
    validator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

# Initialiser la base de données
with app.app_context():
    # Si la base de données existe déjà, la supprimer
    db_path = 'web_portal.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Base de données existante supprimée: {db_path}")
    
    # Crée les tables
    db.create_all()
    print("Tables créées dans la base de données")
    
    # Crée l'utilisateur gestionnaire
    manager = User(
        username='gestionnaire',
        email='gestionnaire@example.com',
        first_name='Gestionnaire',
        last_name='',
        role='manager'
    )
    manager.set_password('password')
    db.session.add(manager)
    print("Utilisateur gestionnaire créé")
    
    # Crée l'utilisateur employee
    employee = User(
        username='employe',
        email='employe@example.com',
        first_name='Employé',
        last_name='',
        role='employee'
    )
    employee.set_password('password')
    db.session.add(employee)
    print("Utilisateur employe créé")
    
    # Sauvegarde les changements
    db.session.commit()
    
    print("Base de données initialisée avec succès!")