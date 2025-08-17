from flask import Blueprint, render_template, redirect, url_for, flash, request, session, send_file, Response
from app import db
from app.models.user import User
from app.models.timesheet import Timesheet
from app.models.audit_log import AuditLog
from app.util import login_required, role_required
from datetime import datetime, timedelta
from sqlalchemy import func
import io
import csv
from app.utils.audit import log_audit

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@role_required('admin')
def dashboard():
    """Tableau de bord administrateur avec statistiques globales."""
    user = User.query.get(session['user_id'])
    
    # Statistiques utilisateurs
    employee_count = User.query.filter_by(role='employee').count()
    manager_count = User.query.filter_by(role='manager').count()
    admin_count = User.query.filter_by(role='admin').count()
    
    # Statistiques feuilles de temps
    total_timesheets = Timesheet.query.count()
    pending_timesheets = Timesheet.query.filter_by(status='submitted').count()
    approved_timesheets = Timesheet.query.filter_by(status='approved').count()
    rejected_timesheets = Timesheet.query.filter_by(status='rejected').count()
    
    # Statistiques heures totales (tous utilisateurs confondus)
    first_day = datetime.today().replace(day=1)
    monthly_timesheets = Timesheet.query.filter(Timesheet.date >= first_day).all()
    total_hours = sum(timesheet.total_hours() for timesheet in monthly_timesheets)
    
    return render_template('admin/dashboard.html', 
                          title='Tableau de bord Admin',
                          current_user=user,
                          employee_count=employee_count,
                          manager_count=manager_count,
                          admin_count=admin_count,
                          total_timesheets=total_timesheets,
                          pending_timesheets=pending_timesheets,
                          approved_timesheets=approved_timesheets,
                          rejected_timesheets=rejected_timesheets,
                          total_hours=total_hours)

@admin_bp.route('/users')
@role_required('admin')
def user_list():
    """Liste de tous les utilisateurs avec options de gestion."""
    user = User.query.get(session['user_id'])
    users = User.query.all()
    
    return render_template('admin/user_list.html',
                          title='Gestion des utilisateurs',
                          current_user=user,
                          users=users)

@admin_bp.route('/user/create', methods=['GET', 'POST'])
@role_required('admin')
def create_user():
    """Création d'un nouvel utilisateur."""
    from flask_wtf import FlaskForm
    from wtforms import StringField, PasswordField, SelectField, SubmitField
    from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
    
    class UserForm(FlaskForm):
        username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=3, max=64)])
        email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
        first_name = StringField('Prénom', validators=[DataRequired(), Length(max=64)])
        last_name = StringField('Nom', validators=[DataRequired(), Length(max=64)])
        password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=6)])
        confirm_password = PasswordField('Confirmer le mot de passe', 
                                        validators=[DataRequired(), EqualTo('password')])
        role = SelectField('Rôle', choices=[
            ('employee', 'Employé'),
            ('manager', 'Manager'),
            ('admin', 'Administrateur')
        ])
        submit = SubmitField('Créer utilisateur')
        
        def validate_username(self, username):
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Ce nom d\'utilisateur est déjà pris.')
                
        def validate_email(self, email):
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Cet email est déjà utilisé.')
    
    user = User.query.get(session['user_id'])
    form = UserForm()
    
    if form.validate_on_submit():
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role=form.role.data
        )
        new_user.set_password(form.password.data)
        
        db.session.add(new_user)
        db.session.commit()
        
        log_audit(
            action='create',
            resource='user',
            resource_id=new_user.id,
            details={
                "username": new_user.username,
                "email": new_user.email,
                "role": new_user.role
            }
        )

        flash(f'Utilisateur {new_user.username} créé avec succès!', 'success')
        return redirect(url_for('admin.user_list'))
        
    return render_template('admin/user_form.html',
                          title='Création d\'utilisateur',
                          current_user=user,
                          form=form,
                          is_edit=False)

@admin_bp.route('/user/edit/<int:id>', methods=['GET', 'POST'])
@role_required('admin')
def edit_user(id):
    """Édition d'un utilisateur existant."""
    from flask_wtf import FlaskForm
    from wtforms import StringField, SelectField, SubmitField, PasswordField
    from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo, ValidationError
    
    class EditUserForm(FlaskForm):
        username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=3, max=64)])
        email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
        first_name = StringField('Prénom', validators=[DataRequired(), Length(max=64)])
        last_name = StringField('Nom', validators=[DataRequired(), Length(max=64)])
        role = SelectField('Rôle', choices=[
            ('employee', 'Employé'),
            ('manager', 'Manager'),
            ('admin', 'Administrateur')
        ])
        new_password = PasswordField('Nouveau mot de passe (laisser vide pour conserver)', 
                                   validators=[Optional(), Length(min=6)])
        confirm_password = PasswordField('Confirmer le nouveau mot de passe', 
                                        validators=[EqualTo('new_password')])
        submit = SubmitField('Mettre à jour')
        
        def __init__(self, original_username, original_email, *args, **kwargs):
            super(EditUserForm, self).__init__(*args, **kwargs)
            self.original_username = original_username
            self.original_email = original_email
            
        def validate_username(self, username):
            if username.data != self.original_username:
                user = User.query.filter_by(username=username.data).first()
                if user:
                    raise ValidationError('Ce nom d\'utilisateur est déjà pris.')
                    
        def validate_email(self, email):
            if email.data != self.original_email:
                user = User.query.filter_by(email=email.data).first()
                if user:
                    raise ValidationError('Cet email est déjà utilisé.')
    
    current_user = User.query.get(session['user_id'])
    user_to_edit = User.query.get_or_404(id)
    
    # Ne pas permettre de modifier le compte admin principal
    if user_to_edit.role == 'admin' and user_to_edit.id != current_user.id:
        flash('Vous ne pouvez pas modifier un autre compte administrateur.', 'danger')
        return redirect(url_for('admin.user_list'))
        
    form = EditUserForm(user_to_edit.username, user_to_edit.email)
    
    if request.method == 'GET':
        # Pré-remplir le formulaire
        form.username.data = user_to_edit.username
        form.email.data = user_to_edit.email
        form.first_name.data = user_to_edit.first_name
        form.last_name.data = user_to_edit.last_name
        form.role.data = user_to_edit.role
    
    if form.validate_on_submit():

        old_values = {
            "username": user_to_edit.username,
            "email": user_to_edit.email,
            "first_name": user_to_edit.first_name,
            "last_name": user_to_edit.last_name,
            "role": user_to_edit.role
        }

        user_to_edit.username = form.username.data
        user_to_edit.email = form.email.data
        user_to_edit.first_name = form.first_name.data
        user_to_edit.last_name = form.last_name.data
        
        # Ne permettre le changement de rôle que si l'admin ne se modifie pas lui-même
        if user_to_edit.id != current_user.id:
            user_to_edit.role = form.role.data
        
        if form.new_password.data:
            user_to_edit.set_password(form.new_password.data)
            
        new_values = {
            "username": user_to_edit.username,
            "email": user_to_edit.email,
            "first_name": user_to_edit.first_name,
            "last_name": user_to_edit.last_name,
            "role": user_to_edit.role,
            "password_changed": bool(form.new_password.data)
        }

        log_audit(
            action='update',
            resource='user',
            resource_id=user_to_edit.id,
            details={
                "old": old_values,
                "new": new_values
            }
        )

        db.session.commit()
        flash(f'Utilisateur {user_to_edit.username} mis à jour avec succès!', 'success')
        return redirect(url_for('admin.user_list'))
        
    return render_template('admin/user_form.html',
                          title='Modification d\'utilisateur',
                          current_user=current_user,
                          form=form,
                          is_edit=True,
                          user=user_to_edit)

@admin_bp.route('/user/delete/<int:id>', methods=['GET', 'POST'])
@role_required('admin')
def delete_user(id):
    """Suppression d'un utilisateur."""
    current_user = User.query.get(session['user_id'])
    user_to_delete = User.query.get_or_404(id)
    
    # Empêcher la suppression de son propre compte
    if user_to_delete.id == current_user.id:
        flash('Vous ne pouvez pas supprimer votre propre compte.', 'danger')
        return redirect(url_for('admin.user_list'))
        
    # Ne pas permettre de supprimer un autre admin
    if user_to_delete.role == 'admin' and user_to_delete.id != current_user.id:
        flash('Vous ne pouvez pas supprimer un autre compte administrateur.', 'danger')
        return redirect(url_for('admin.user_list'))
        
    # Confirmation requise via POST
    if request.method == 'POST':
        user_info = {
            "id": user_to_delete.id,
            "username": user_to_delete.username,
            "email": user_to_delete.email,
            "role": user_to_delete.role
        }

        # Supprimer les feuilles de temps associées
        Timesheet.query.filter_by(user_id=user_to_delete.id).delete()
        Timesheet.query.filter_by(validator_id=user_to_delete.id).update({Timesheet.validator_id: None})
        
        username = user_to_delete.username
        db.session.delete(user_to_delete)
        db.session.commit()
        
        log_audit(
            action='delete',
            resource='user',
            details=user_info
        )

        flash(f'Utilisateur {username} supprimé avec succès.', 'success')
        return redirect(url_for('admin.user_list'))
        
    return render_template('admin/confirm_delete.html',
                          title='Supprimer utilisateur',
                          current_user=current_user,
                          user=user_to_delete)

@admin_bp.route('/reports')
@role_required('admin')
def reports():
    """Page principale des rapports administratifs."""
    user = User.query.get(session['user_id'])
    
    return render_template('admin/reports.html',
                          title='Rapports administratifs',
                          current_user=user)

@admin_bp.route('/system')
@role_required('admin')
def system():
    """Informations système et configuration."""
    import platform
    import os
    from sqlalchemy import inspect
    
    user = User.query.get(session['user_id'])
    
    # Informations système
    system_info = {
        'os': platform.system(),
        'python_version': platform.python_version(),
        'db_type': db.engine.name,
        'db_version': db.engine.dialect.server_version_info if hasattr(db.engine.dialect, 'server_version_info') else 'Unknown'
    }
    
    # Tables dans la base de données
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    # Variables d'environnement (filtrer les sensibles)
    env_vars = {k: '***' if k in ('SECRET_KEY', 'DATABASE_URI') else v 
               for k, v in os.environ.items()}
               
    return render_template('admin/system.html',
                          title='Informations système',
                          current_user=user,
                          system_info=system_info,
                          tables=tables,
                          env_vars=env_vars)

@admin_bp.route('/reports/activity')
@role_required('admin')
def user_activity_report():
    """Génère un rapport d'activité des utilisateurs."""
    user = User.query.get(session['user_id'])
    
    # Calcul de la période (par défaut, les 30 derniers jours)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Récupérer les données
    user_data = []
    all_users = User.query.all()
    
    for u in all_users:
        # Feuilles de temps soumises dans la période
        submitted_count = Timesheet.query.filter(
            Timesheet.user_id == u.id,
            Timesheet.date >= start_date,
            Timesheet.date <= end_date
        ).count()
        
        # Heures totales dans la période
        timesheets = Timesheet.query.filter(
            Timesheet.user_id == u.id,
            Timesheet.date >= start_date,
            Timesheet.date <= end_date,
            Timesheet.status == 'approved'
        ).all()
        
        total_hours = sum(ts.total_hours() for ts in timesheets)
        
        user_data.append({
            'id': u.id,
            'username': u.username,
            'full_name': f"{u.first_name} {u.last_name}",
            'role': u.role,
            'submitted_count': submitted_count,
            'total_hours': total_hours
        })
    
    return render_template('admin/report_activity.html',
                          title='Rapport d\'activité',
                          current_user=user,
                          user_data=user_data,
                          start_date=start_date,
                          end_date=end_date)

@admin_bp.route('/reports/hours')
@role_required('admin')
def global_hours_report():
    """Génère un rapport des heures globales."""
    user = User.query.get(session['user_id'])
    
    # Par défaut, rapport pour le mois en cours
    today = datetime.today()
    first_day = today.replace(day=1)
    last_day = today
    
    # Statistiques par jour
    days = {}
    
    # Récupérer toutes les feuilles approuvées du mois
    timesheets = Timesheet.query.filter(
        Timesheet.date >= first_day,
        Timesheet.date <= last_day,
        Timesheet.status == 'approved'
    ).all()
    
    # Calculer les heures par jour
    for ts in timesheets:
        day_str = ts.date.strftime('%Y-%m-%d')
        if day_str not in days:
            days[day_str] = 0
        
        days[day_str] += ts.total_hours()
    
    # Trier par date
    sorted_days = sorted(days.items())
    
    # Calculer le total général
    total_hours = sum(days.values())
    
    # Grouper par rôle
    role_hours = {}
    for ts in timesheets:
        user_role = User.query.get(ts.user_id).role
        if user_role not in role_hours:
            role_hours[user_role] = 0
        
        role_hours[user_role] += ts.total_hours()
    
    return render_template('admin/report_hours.html',
                          title='Rapport des heures',
                          current_user=user,
                          days=sorted_days,
                          total_hours=total_hours,
                          role_hours=role_hours,
                          first_day=first_day,
                          last_day=last_day)

@admin_bp.route('/reports/system_audit')
@role_required('admin')
def system_audit_report():
    """Génère un rapport d'audit système."""
    user = User.query.get(session['user_id'])
    
    # Ici, vous pourriez implémenter un vrai système d'audit
    # Pour l'instant, on génère juste des statistiques de base
    
    # Statistiques utilisateurs
    user_stats = {
        'total': User.query.count(),
        'by_role': {
            'admin': User.query.filter_by(role='admin').count(),
            'manager': User.query.filter_by(role='manager').count(),
            'employee': User.query.filter_by(role='employee').count()
        }
    }
    
    # Statistiques des feuilles de temps
    timesheet_stats = {
        'total': Timesheet.query.count(),
        'approved': Timesheet.query.filter_by(status='approved').count(),
        'rejected': Timesheet.query.filter_by(status='rejected').count(),
        'pending': Timesheet.query.filter_by(status='submitted').count()
    }
    
    return render_template('admin/report_audit.html',
                          title='Audit système',
                          current_user=user,
                          user_stats=user_stats,
                          timesheet_stats=timesheet_stats,
                          timestamp=datetime.now())

@admin_bp.route('/export/users/<format>')
@role_required('admin')
def export_users(format):
    """Exporte la liste des utilisateurs au format spécifié."""
    users = User.query.all()
    
    if format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        
        # En-tête
        writer.writerow(['ID', 'Nom d\'utilisateur', 'Email', 'Prénom', 'Nom', 'Rôle'])
        
        # Données
        for user in users:
            writer.writerow([
                user.id,
                user.username,
                user.email,
                user.first_name,
                user.last_name,
                user.role
            ])
        
        output.seek(0)
        
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=users_export.csv"}
        )
    
    elif format == 'json':
        import json
        
        users_data = [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role
        } for user in users]
        
        return Response(
            json.dumps(users_data, indent=4),
            mimetype="application/json",
            headers={"Content-Disposition": "attachment;filename=users_export.json"}
        )
    
    else:
        flash(f"Format d'export '{format}' non supporté", "danger")
        return redirect(url_for('admin.reports'))

@admin_bp.route('/export/timesheets/<format>')
@role_required('admin')
def export_timesheets(format):
    """Exporte la liste des feuilles de temps au format spécifié."""
    timesheets = Timesheet.query.all()
    
    if format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        
        # En-tête
        writer.writerow(['ID', 'Utilisateur', 'Date', 'Début', 'Fin', 'Pause', 'Heures', 'Statut'])
        
        # Données
        for ts in timesheets:
            user = User.query.get(ts.user_id)
            
            writer.writerow([
                ts.id,
                f"{user.first_name} {user.last_name}",
                ts.date.strftime('%Y-%m-%d'),
                ts.start_time.strftime('%H:%M'),
                ts.end_time.strftime('%H:%M'),
                ts.break_duration,
                f"{ts.total_hours():.2f}",
                ts.status
            ])
        
        output.seek(0)
        
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=timesheets_export.csv"}
        )
    
    elif format == 'json':
        import json
        
        ts_data = []
        for ts in timesheets:
            user = User.query.get(ts.user_id)
            
            ts_data.append({
                'id': ts.id,
                'user': {
                    'id': user.id,
                    'name': f"{user.first_name} {user.last_name}"
                },
                'date': ts.date.strftime('%Y-%m-%d'),
                'start_time': ts.start_time.strftime('%H:%M'),
                'end_time': ts.end_time.strftime('%H:%M'),
                'break_duration': ts.break_duration,
                'total_hours': f"{ts.total_hours():.2f}",
                'status': ts.status
            })
        
        return Response(
            json.dumps(ts_data, indent=4),
            mimetype="application/json",
            headers={"Content-Disposition": "attachment;filename=timesheets_export.json"}
        )
    
    else:
        flash(f"Format d'export '{format}' non supporté", "danger")
        return redirect(url_for('admin.reports'))

@admin_bp.route('/export/complete/<format>')
@role_required('admin')
def export_complete(format):
    """Exporte toutes les données de l'application au format spécifié."""
    users = User.query.all()
    timesheets = Timesheet.query.all()
    
    if format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        
        # PARTIE 1: Utilisateurs
        writer.writerow(['--- UTILISATEURS ---'])
        writer.writerow(['ID', 'Nom d\'utilisateur', 'Email', 'Prénom', 'Nom', 'Rôle'])
        
        for user in users:
            writer.writerow([
                user.id,
                user.username,
                user.email,
                user.first_name,
                user.last_name,
                user.role
            ])
        
        # Ligne vide de séparation
        writer.writerow([])
        
        # PARTIE 2: Feuilles de temps
        writer.writerow(['--- FEUILLES DE TEMPS ---'])
        writer.writerow(['ID', 'Utilisateur ID', 'Nom utilisateur', 'Date', 'Début', 'Fin', 'Pause', 'Heures', 'Statut'])
        
        for ts in timesheets:
            user = User.query.get(ts.user_id)
            
            writer.writerow([
                ts.id,
                ts.user_id,
                f"{user.first_name} {user.last_name}",
                ts.date.strftime('%Y-%m-%d'),
                ts.start_time.strftime('%H:%M'),
                ts.end_time.strftime('%H:%M'),
                ts.break_duration,
                f"{ts.total_hours():.2f}",
                ts.status
            ])
        
        output.seek(0)
        
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=timeportal_export_complete.csv"}
        )
    
    elif format == 'json':
        import json
        
        # Structure complète des données
        data = {
            'exportDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'users': [{
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role
            } for user in users],
            'timesheets': []
        }
        
        # Ajouter les données des feuilles de temps
        for ts in timesheets:
            user = User.query.get(ts.user_id)
            
            data['timesheets'].append({
                'id': ts.id,
                'user_id': ts.user_id,
                'user_name': f"{user.first_name} {user.last_name}",
                'date': ts.date.strftime('%Y-%m-%d'),
                'start_time': ts.start_time.strftime('%H:%M'),
                'end_time': ts.end_time.strftime('%H:%M'),
                'break_duration': ts.break_duration,
                'total_hours': f"{ts.total_hours():.2f}",
                'status': ts.status,
                'validator_id': ts.validator_id
            })
        
        return Response(
            json.dumps(data, indent=4),
            mimetype="application/json",
            headers={"Content-Disposition": "attachment;filename=timeportal_export_complete.json"}
        )
    
    else:
        flash(f"Format d'export '{format}' non supporté", "danger")
        return redirect(url_for('admin.reports'))
    
@admin_bp.route('/security/audit-logs')
@role_required('admin')
def audit_logs():
    user = User.query.get(session['user_id'])
    """Affiche les journaux d'audit de sécurité."""
    # Paramètres de filtrage
    page = request.args.get('page', 1, type=int)
    action = request.args.get('action', '')
    username = request.args.get('username', '')
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    
    # Construire la requête de base
    query = AuditLog.query
    
    # Appliquer les filtres
    if action:
        query = query.filter(AuditLog.action == action)
    
    if username:
        query = query.filter(AuditLog.username.ilike(f'%{username}%'))
    
    if from_date:
        try:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
            query = query.filter(AuditLog.timestamp >= from_date_obj)
        except ValueError:
            flash('Format de date invalide pour la date de début', 'danger')
    
    if to_date:
        try:
            to_date_obj = datetime.strptime(to_date + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            query = query.filter(AuditLog.timestamp <= to_date_obj)
        except ValueError:
            flash('Format de date invalide pour la date de fin', 'danger')
    
    # Trier par date (plus récent en premier)
    query = query.order_by(AuditLog.timestamp.desc())
    
    # Pagination
    per_page = 50  # Nombre d'entrées par page
    logs = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Actions distinctes pour le filtre
    distinct_actions = db.session.query(AuditLog.action).distinct().all()
    actions = [action[0] for action in distinct_actions]
    
    # Utilisateurs distincts pour le filtre (limité aux 100 plus actifs)
    distinct_usernames = db.session.query(AuditLog.username, db.func.count(AuditLog.id).label('count')) \
                                .group_by(AuditLog.username) \
                                .order_by(db.text('count DESC')) \
                                .limit(100) \
                                .all()
    usernames = [u[0] for u in distinct_usernames if u[0]]
    
    return render_template('admin/audit_logs.html',
                          title='Journaux de sécurité',
                          logs=logs,
                          actions=actions,
                          usernames=usernames,
                          current_user=user,
                          current_filters={
                              'action': action,
                              'username': username,
                              'from_date': from_date,
                              'to_date': to_date
                          })

@admin_bp.route('/security/audit-logs/export')
@role_required('admin')
def export_audit_logs():
    """Exporte les journaux d'audit au format CSV."""
    # Paramètres de filtrage (similaires à la route audit_logs)
    action = request.args.get('action', '')
    username = request.args.get('username', '')
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    
    # Construire la requête avec les mêmes filtres
    query = AuditLog.query
    
    if action:
        query = query.filter(AuditLog.action == action)
    
    if username:
        query = query.filter(AuditLog.username.ilike(f'%{username}%'))
    
    if from_date:
        try:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
            query = query.filter(AuditLog.timestamp >= from_date_obj)
        except ValueError:
            pass
    
    if to_date:
        try:
            to_date_obj = datetime.strptime(to_date + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            query = query.filter(AuditLog.timestamp <= to_date_obj)
        except ValueError:
            pass
    
    # Trier par date (plus ancien en premier pour l'export)
    query = query.order_by(AuditLog.timestamp)
    
    # Récupérer tous les logs correspondants
    logs = query.all()
    
    # Préparer le CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # En-tête
    writer.writerow(['ID', 'Date/Heure', 'Utilisateur', 'Action', 'Ressource', 'ID Ressource', 'Adresse IP', 'Agent utilisateur', 'Détails'])
    
    # Données
    for log in logs:
        writer.writerow([
            log.id,
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.username or 'Anonymous',
            log.action,
            log.resource,
            log.resource_id or '',
            log.ip_address or '',
            log.user_agent or '',
            log.details or ''
        ])
    
    output.seek(0)
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=audit_logs_{datetime.now().strftime('%Y%m%d')}.csv"}
    )