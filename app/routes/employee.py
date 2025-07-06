from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app import db
from app.models.timesheet import Timesheet
from app.models.user import User
from app.util import login_required, role_required
from flask_wtf import FlaskForm
from wtforms import DateField, TimeField, IntegerField, StringField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange, Length
from datetime import datetime, date
from app.utils.audit import log_audit

employee_bp = Blueprint('employee', __name__, url_prefix='/employee')

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

@employee_bp.route('/timesheet/new', methods=['GET', 'POST'])
@role_required('employee')
def new_timesheet():
    user = User.query.get(session['user_id'])
    form = TimesheetForm()
    
    if form.validate_on_submit():
        timesheet = Timesheet(
            user_id=user.id,
            date=form.date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            break_duration=form.break_duration.data,
            description=form.description.data
        )
        db.session.add(timesheet)
        db.session.commit()

        log_audit(
            action='create',
            resource='timesheet',
            resource_id=timesheet.id,
            details={
                "date": timesheet.date.strftime('%Y-%m-%d'),
                "hours": "%.2f" % timesheet.total_hours()
            }
        )
        flash('Feuille de temps enregistrée avec succès')
        return redirect(url_for('employee.dashboard'))
        
    return render_template('employee/timesheet_form.html', 
                          title='Nouvelle feuille de temps', 
                          form=form,
                          current_user=user,
                          is_edit=False,
                          timesheet=None)

@employee_bp.route('/timesheets')
@role_required('employee')
def list_timesheets():
    user = User.query.get(session['user_id'])
    # Récupérer toutes les feuilles de temps de l'employé
    timesheets = Timesheet.query.filter_by(user_id=session['user_id']).order_by(Timesheet.date.desc()).all()
    
    return render_template('employee/timesheet_list.html', 
                          title='Mes feuilles de temps', 
                          current_user=user,
                          timesheets=timesheets)

@employee_bp.route('/timesheet/edit/<int:id>', methods=['GET', 'POST'])
@role_required('employee')
def edit_timesheet(id):
    user = User.query.get(session['user_id'])
    
    # Récupérer la feuille de temps
    timesheet = Timesheet.query.get_or_404(id)
    
    # Vérifier que la feuille appartient à l'employé connecté
    if timesheet.user_id != user.id:
        flash('Vous n\'êtes pas autorisé à modifier cette feuille de temps', 'danger')
        return redirect(url_for('employee.dashboard'))
    
    # Vérifier que la feuille n'est pas déjà approuvée/rejetée
    if timesheet.status != 'submitted':
        flash('Cette feuille de temps ne peut plus être modifiée car elle a déjà été traitée', 'warning')
        return redirect(url_for('employee.list_timesheets'))
    
    # Préparer le formulaire
    form = TimesheetForm(obj=timesheet)
    
    if form.validate_on_submit():

        old_values = {
            "date": timesheet.date.strftime('%Y-%m-%d'),
            "start_time": timesheet.start_time.strftime('%H:%M'),
            "end_time": timesheet.end_time.strftime('%H:%M'),
            "break_duration": timesheet.break_duration,
            "hours": "%.2f" % timesheet.total_hours()
        }

        # Mettre à jour les données
        form.populate_obj(timesheet)
        db.session.commit()

        new_values = {
            "date": timesheet.date.strftime('%Y-%m-%d'),
            "start_time": timesheet.start_time.strftime('%H:%M'),
            "end_time": timesheet.end_time.strftime('%H:%M'),
            "break_duration": timesheet.break_duration,
            "hours": "%.2f" % timesheet.total_hours()
        }

        log_audit(
            action='update',
            resource='timesheet',
            resource_id=timesheet.id,
            details={
                "old": old_values,
                "new": new_values
            }
        )
        
        flash('Feuille de temps mise à jour avec succès', 'success')
        return redirect(url_for('employee.list_timesheets'))
        
    return render_template('employee/timesheet_form.html', 
                          title='Modifier la feuille de temps', 
                          form=form,
                          current_user=user,
                          is_edit=True,
                          timesheet=timesheet)