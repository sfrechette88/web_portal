from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(512))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    role = db.Column(db.String(20))  # 'employee' ou 'manager'
    employee_type = db.Column(db.String(20), default='regulier')  # 'regulier' ou 'hebdomadaire'
    
    # Relation avec les feuilles de temps (un utilisateur peut avoir plusieurs feuilles de temps)
    timesheets = db.relationship('Timesheet', backref='user', lazy='dynamic',
                                foreign_keys='Timesheet.user_id')
    
    # Relation pour les feuilles validées
    validated_timesheets = db.relationship('Timesheet', backref='validator', lazy='dynamic',
                                         foreign_keys='Timesheet.validator_id')
    
    # Ajouter cette relation
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic',
                                foreign_keys='AuditLog.user_id')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)