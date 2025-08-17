from app import db

class Code(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(64), unique=True, nullable=False)

class Modifier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(64), unique=True, nullable=False)
    valeur_minutes = db.Column(db.Integer, default=0)  # Pour appliquer un effet sur le temps si besoin
