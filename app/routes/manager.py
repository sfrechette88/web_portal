from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app import db
from app.models.timesheet import Timesheet
from app.models.user import User
from app.util import login_required, role_required
from sqlalchemy import func
from datetime import datetime, timedelta
from app.utils.audit import log_audit
from werkzeug.security import generate_password_hash

manager_bp = Blueprint('manager', __name__, url_prefix='/manager')

@manager_bp.route('/dashboard')
@role_required('manager')
def dashboard():
    user = User.query.get(session['user_id'])
    
    # Nombre total d'employés
    employee_count = User.query.filter_by(role='employee').count()
    
    # Nombre de feuilles de temps en attente d'approbation
    pending_count = Timesheet.query.filter_by(status='submitted').count()
    
    # Heures totales pour le mois en cours - Calculé manuellement
    first_day = datetime.today().replace(day=1)
    approved_timesheets = Timesheet.query.filter(
        Timesheet.date >= first_day,
        Timesheet.status == 'approved'
    ).all()
    
    total_hours = 0
    for timesheet in approved_timesheets:
        total_hours += timesheet.total_hours()
    
    return render_template('manager/dashboard.html', 
                          title='Tableau de bord manager', 
                          current_user=user,
                          employee_count=employee_count,
                          pending_count=pending_count,
                          total_hours=total_hours,
                          now=datetime.now())

@manager_bp.route('/timesheets/pending')
@role_required('manager')
def pending_timesheets():
    user = User.query.get(session['user_id'])
    # Récupérer toutes les feuilles de temps en attente
    timesheets = Timesheet.query.filter_by(status='submitted').order_by(Timesheet.date.desc()).all()
    
    return render_template('manager/pending_timesheets.html', 
                          title='Feuilles de temps en attente',
                          current_user=user, 
                          timesheets=timesheets)

@manager_bp.route('/timesheet/<int:id>/approve')
@role_required('manager')
def approve_timesheet(id):
    timesheet = Timesheet.query.get_or_404(id)
    timesheet.status = 'approved'
    timesheet.validator_id = session['user_id']
    db.session.commit()

    log_audit(
        action='approve',
        resource='timesheet',
        resource_id=timesheet.id,
        details={
            "user_id": timesheet.user_id,
            "date": timesheet.date.strftime('%Y-%m-%d'),
            "hours": "%.2f" % timesheet.total_hours()
        }
    )
    
    flash('Feuille de temps approuvée')
    return redirect(url_for('manager.pending_timesheets'))

@manager_bp.route('/timesheet/<int:id>/reject')
@role_required('manager')
def reject_timesheet(id):
    timesheet = Timesheet.query.get_or_404(id)
    timesheet.status = 'rejected'
    timesheet.validator_id = session['user_id']
    db.session.commit()

    log_audit(
        action='reject',
        resource='timesheet',
        resource_id=timesheet.id,
        details={
            "user_id": timesheet.user_id,
            "date": timesheet.date.strftime('%Y-%m-%d'),
            "hours": "%.2f" % timesheet.total_hours()
        }
    )
    
    flash('Feuille de temps rejetée')
    return redirect(url_for('manager.pending_timesheets'))

from app.models.timesheet import Timesheet  # Assure-toi que ce import est présent

@manager_bp.route('/employees')
@role_required('manager')
def employee_list():
    user = User.query.get(session['user_id'])
    employees = User.query.filter_by(role='employee').all()
    
    # Pour les statistiques du mois en cours
    first_day_of_month = datetime.today().replace(day=1)
    
    # Pré-calculer les statistiques pour chaque employé
    employee_stats = []
    for employee in employees:
        # Nombre de feuilles ce mois
        timesheet_count = Timesheet.query.filter(
            Timesheet.user_id == employee.id,
            Timesheet.date >= first_day_of_month
        ).count()
        
        # Heures approuvées ce mois
        approved_timesheets = Timesheet.query.filter(
            Timesheet.user_id == employee.id,
            Timesheet.date >= first_day_of_month,
            Timesheet.status == 'approved'
        ).all()
        
        total_hours = sum(ts.total_hours() for ts in approved_timesheets)
        
        employee_stats.append({
            'employee': employee,
            'timesheet_count': timesheet_count,
            'total_hours': total_hours
        })
    
    return render_template('manager/employee_list.html', 
                          title='Liste des employés', 
                          current_user=user,
                          employee_stats=employee_stats,
                          first_day_of_month=first_day_of_month)

@manager_bp.route('/reports/hours')
@role_required('manager')
def hours_report():
    user = User.query.get(session['user_id'])
    
    # Rapport des heures par employé pour le mois en cours
    first_day = datetime.today().replace(day=1)
    
    # Récupérer tous les employés
    employees = User.query.filter_by(role='employee').all()
    
    # Préparer les données pour le template
    employee_hours = []
    total_all_hours = 0
    
    for employee in employees:
        # Récupérer toutes les feuilles de temps approuvées pour cet employé ce mois-ci
        timesheets = Timesheet.query.filter(
            Timesheet.user_id == employee.id,
            Timesheet.date >= first_day,
            Timesheet.status == 'approved'
        ).all()
        
        # Calculer le total des heures
        hours_sum = sum(timesheet.total_hours() for timesheet in timesheets)
        total_all_hours += hours_sum
        
        # Ajouter aux résultats
        employee_hours.append({
            'id': employee.id,
            'first_name': employee.first_name,
            'last_name': employee.last_name,
            'total_hours': hours_sum
        })
    
    return render_template('manager/hours_report.html', 
                          title='Rapport des heures', 
                          current_user=user,
                          employee_hours=employee_hours,
                          total_all_hours=total_all_hours,
                          month=first_day.strftime('%B %Y'))


@manager_bp.route('/employee/<int:id>/timesheets')
@role_required('manager')
def view_employee_timesheets(id):
    user = User.query.get(session['user_id'])
    employee = User.query.get_or_404(id)
    
    # Vérifier que c'est bien un employé
    if employee.role != 'employee':
        flash('Cet utilisateur n\'est pas un employé', 'danger')
        return redirect(url_for('manager.employee_list'))
    
    # Récupérer les feuilles de temps de l'employé
    timesheets = Timesheet.query.filter_by(user_id=employee.id).order_by(Timesheet.date.desc()).all()
    
    return render_template('manager/employee_timesheets.html', 
                          title=f'Feuilles de temps - {employee.first_name} {employee.last_name}', 
                          current_user=user,
                          employee=employee,
                          timesheets=timesheets)

@manager_bp.route('/employee/add', methods=['GET', 'POST'])
@role_required('manager')
def add_employee():
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        password = request.form.get('password')

        role = request.form.get('role')
        employee_type = request.form.get('employee_type')

        # Vérifications simples (à peaufiner pour la prod)
        if not all([username, email, first_name, last_name, password]):
            flash('Tous les champs sont obligatoires.', 'danger')
            return redirect(url_for('manager.add_employee'))

        if User.query.filter_by(username=username).first():
            flash('Nom d’utilisateur déjà utilisé.', 'danger')
            return redirect(url_for('manager.add_employee'))

        if User.query.filter_by(email=email).first():
            flash('Courriel déjà utilisé.', 'danger')
            return redirect(url_for('manager.add_employee'))

        new_user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role='employee'
        )
        new_user.password_hash = generate_password_hash(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Employé ajouté avec succès!', 'success')
        return redirect(url_for('manager.employee_list'))

    return render_template(
        'manager/add_employee.html',
        title='Ajouter un employé',
        current_user=user
        )