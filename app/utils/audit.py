from app import db
from app.models.audit_log import AuditLog
from flask import request, session
import json
from datetime import datetime

def log_audit(action, resource, resource_id=None, user_id=None, username=None, details=None):
    """
    Enregistre une entrée dans le journal d'audit.
    
    Args:
        action (str): L'action effectuée (login, logout, create, update, delete)
        resource (str): La ressource concernée (user, timesheet)
        resource_id (int, optional): L'ID de la ressource
        user_id (int, optional): L'ID de l'utilisateur (si connecté)
        username (str, optional): Le nom d'utilisateur (pour les tentatives de connexion échouées)
        details (dict, optional): Détails supplémentaires à stocker en JSON
    """
    # Si l'utilisateur est connecté et que user_id n'est pas fourni
    if user_id is None and 'user_id' in session:
        user_id = session['user_id']
        
    # Si user_id est fourni mais pas username
    if user_id is not None and username is None:
        from app.models.user import User
        user = User.query.get(user_id)
        if user:
            username = user.username
    
    # Conversion des détails en JSON si c'est un dictionnaire
    details_json = None
    if details:
        if isinstance(details, dict):
            details_json = json.dumps(details)
        else:
            details_json = str(details)
    
    # Création du log
    log = AuditLog(
        timestamp=datetime.utcnow(),
        user_id=user_id,
        username=username,
        action=action,
        resource=resource,
        resource_id=resource_id,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string if request.user_agent else None,
        details=details_json
    )
    
    db.session.add(log)
    db.session.commit()
    
    return log