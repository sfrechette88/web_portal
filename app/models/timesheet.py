from datetime import datetime
from app import db

class Timesheet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.Date, index=True)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    break_duration = db.Column(db.Integer, default=0)  # Durée de pause en minutes
    description = db.Column(db.String(200))
    status = db.Column(db.String(20), default='submitted')  # 'submitted', 'approved', 'rejected'

    # Nouveau : code de la journée (ex: Présence, Vacances, etc.)
    code_id = db.Column(db.Integer, db.ForeignKey('code.id'), nullable=True)
    code = db.relationship('Code', backref='timesheets')

    # Validateur (manager qui a approuvé/rejeté la feuille de temps)
    validator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # Relation vers les modificateurs associés à ce timesheet
    modificateurs = db.relationship('TimesheetModifier', back_populates='timesheet', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Timesheet {self.id} - {self.date}>'

    def total_hours(self):
        """Calcule le nombre d'heures travaillées (en tenant compte des pauses)"""
        if not self.start_time or not self.end_time:
            return 0

        start_datetime = datetime.combine(self.date, self.start_time)
        end_datetime = datetime.combine(self.date, self.end_time)
        total_seconds = (end_datetime - start_datetime).total_seconds()

        # Soustraction de la durée de pause (en secondes)
        total_seconds -= self.break_duration * 60

        # Application des modificateurs (exemple : soustraction pour “repas”)
        for mod_assoc in self.modificateurs:
            mod = mod_assoc.modifier
            if mod and mod.valeur_minutes:
                total_seconds += mod.valeur_minutes * 60  # Peut être négatif

        # Conversion en heures
        return max(0, total_seconds / 3600)

class TimesheetModifier(db.Model):
    __tablename__ = 'timesheet_modifier'
    id = db.Column(db.Integer, primary_key=True)
    timesheet_id = db.Column(db.Integer, db.ForeignKey('timesheet.id'))
    modifier_id = db.Column(db.Integer, db.ForeignKey('modifier.id'))

    # Relations pour accès facile
    timesheet = db.relationship('Timesheet', back_populates='modificateurs')
    modifier = db.relationship('Modifier')

    def __repr__(self):
        return f'<TimesheetModifier {self.timesheet_id} - {self.modifier_id}>'
