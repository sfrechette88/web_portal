from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app import db
from app.models.timesheet import Timesheet
from app.models.user import User
from app.util import login_required, role_required
from flask_wtf import FlaskForm
from wtforms import DateField, TimeField, IntegerField, StringField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange, Length
from datetime import datetime, date, timedelta
from app.utils.audit import log_audit
from app.models.code import Code, Modifier

employee_bp = Blueprint('employee', __name__, url_prefix='/employee')

def get_period_dates(period_num, year):
    # Tu dois adapter le calcul du début de la première période selon ton année fiscale !
    # Ici, on considère que la première période commence le lundi de la 1re semaine de l'année.
    start_of_year = date(year, 1, 1)
    while start_of_year.weekday() != 0:  # 0 = lundi
        start_of_year += timedelta(days=1)
    start = start_of_year + timedelta(weeks=(period_num - 1) * 2)
    days = [start + timedelta(days=i) for i in range(14)]
    return days

class TimesheetForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()], default=date.today)
    start_time = TimeField('Heure de début', validators=[DataRequired()])
    end_time = TimeField('Heure de fin', validators=[DataRequired()])
    break_duration = IntegerField('Durée de pause (minutes)', validators=[Optional(), NumberRange(min=0)], default=0)
    description = StringField('Description', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Enregistrer')

@employee_bp.route('/dashboard')
@role_required('employee')
def dashboard():
    user = User.query.get(session['user_id'])
    # Récupérer les feuilles de temps récentes de l'employé
    recent_timesheets = Timesheet.query.filter_by(user_id=user.id).order_by(Timesheet.date.desc()).limit(5).all()
    
    return render_template('employee/dashboard.html', 
                          title='Tableau de bord', 
                          user=user,
                          current_user=user,
                          recent_timesheets=recent_timesheets)


@employee_bp.route('/timesheet', methods=['GET', 'POST'])
@role_required('employee')
def timesheet():
    user = User.query.get(session['user_id'])
    year = date.today().year

    # Période courante par défaut
    period = request.args.get('period', type=int)
    if not period:
        today = date.today()
        start_of_year = date(year, 1, 1)
        while start_of_year.weekday() != 0:
            start_of_year += timedelta(days=1)
        weeks_since = (today - start_of_year).days // 7
        period = (weeks_since // 2) + 1
        period = min(max(1, period), 26)
        return redirect(url_for('employee.timesheet', period=period))

    days = get_period_dates(period, year)
    weeks = [days[:7], days[7:]]

    codes = Code.query.all()
    modifiers = Modifier.query.all()

    # readonly si période passée (à ajuster selon ta logique)
    today = date.today()
    periode_debut = days[0]
    periode_fin = days[-1]
    readonly = periode_fin < today

    # 1️⃣ SAUVEGARDE DES DONNÉES
    if request.method == 'POST' and not readonly:
        for day in days:
            start = request.form.get(f"start_{day}")
            end = request.form.get(f"end_{day}")
            code_id = request.form.get(f"code_{day}")

            if not (start and end and code_id):
                continue

            ts = Timesheet.query.filter_by(user_id=user.id, date=day).first()
            if not ts:
                ts = Timesheet(user_id=user.id, date=day)
                db.session.add(ts)
            ts.start_time = start
            ts.end_time = end
            ts.code_id = code_id
            ts.status = 'submitted'

        db.session.commit()
        flash("Feuille de temps sauvegardée.", "success")
        return redirect(url_for('employee.timesheet', period=period))

    # 2️⃣ PRÉPARATION DES DONNÉES POUR AFFICHAGE
    timesheet_data = {}
    for day in days:
        ts = Timesheet.query.filter_by(user_id=user.id, date=day).first()
        timesheet_data[day] = ts

    prev_period = period - 1 if period > 1 else 26
    next_period = period + 1 if period < 26 else 1

    return render_template(
        'employee/timesheet.html',
        period_num=period,
        weeks=weeks,
        codes=codes,
        modifiers=modifiers,
        week_start=periode_debut,
        week_end=periode_fin,
        readonly=readonly,
        prev_period=prev_period,
        next_period=next_period,
        timesheet_data=timesheet_data,
        current_user=user
    )
