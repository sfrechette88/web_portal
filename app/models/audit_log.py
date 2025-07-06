from datetime import datetime
from app import db

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    username = db.Column(db.String(64))  # Pour stocker aussi les tentatives de connexion avec des utilisateurs inexistants
    action = db.Column(db.String(128))   # Le type d'action (login, logout, create, update, delete, etc.)
    resource = db.Column(db.String(64))  # La ressource concernée (user, timesheet, etc.)
    resource_id = db.Column(db.Integer, nullable=True)  # L'ID de la ressource (si applicable)
    ip_address = db.Column(db.String(45))  # IPv6 peut aller jusqu'à 45 caractères
    user_agent = db.Column(db.String(256), nullable=True)  # Le navigateur/client utilisé
    details = db.Column(db.Text, nullable=True)  # Détails supplémentaires en JSON ou texte
    
    def __repr__(self):
        return f'<AuditLog {self.timestamp} {self.action} by {self.username or "Anonymous"}>'