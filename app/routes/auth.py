from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app import db
from app.models.user import User
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from app.utils.audit import log_audit

auth_bp = Blueprint('auth', __name__)

class LoginForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    remember_me = BooleanField('Se souvenir de moi')
    submit = SubmitField('Connexion')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        # Rediriger vers la page appropriée selon le rôle
        if session['role'] == 'manager':
            return redirect(url_for('manager.dashboard'))
        elif session['role'] == 'admin':  # Ajouter cette condition
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('employee.dashboard'))
            
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            log_audit(
                action='login_failed',
                resource='auth',
                username=form.username.data,
                details={"reason": "Invalid username or password"}
            )
            flash('Nom d\'utilisateur ou mot de passe invalide')
            return redirect(url_for('auth.login'))
        
        log_audit(
            action='login_success',
            resource='auth',
            user_id=user.id,
            username=user.username
        )
        session['user_id'] = user.id
        session['role'] = user.role
        session['username'] = user.username
        
        next_page = request.args.get('next')
        if not next_page or next_page.startswith('http'):
            # Rediriger vers la page appropriée selon le rôle
            if user.role == 'manager':
                next_page = url_for('manager.dashboard')
            elif user.role == 'admin':  # Ajouter cette condition
                next_page = url_for('admin.dashboard')
            else:
                next_page = url_for('employee.dashboard')
                
        return redirect(next_page)
        
    return render_template('auth/login.html', title='Connexion', form=form)

from flask import current_app
@auth_bp.route('/logout')
def logout():
    # Audit
    if 'user_id' in session:
        log_audit(
            action='logout',
            resource='auth',
            user_id=session['user_id']
        )

    # # Vide toute la session
    session.clear()

    # Récupère le nom du cookie depuis la config
    cookie_name = current_app.config.get('SESSION_COOKIE_NAME', 'session')

    # Prépare la réponse
    resp = redirect(url_for('auth.login'))

    # Force la destruction du cookie de session
    resp.set_cookie(
        key=cookie_name,  # généralement "session"
        value='',                              # vide
        expires=0,                             # date passée = suppression
        path=current_app.config.get('SESSION_COOKIE_PATH', '/'),
        domain=current_app.config.get('SESSION_COOKIE_DOMAIN', None),
        secure=current_app.config.get('SESSION_COOKIE_SECURE', False),
        samesite=current_app.config.get('SESSION_COOKIE_SAMESITE', None)
    )

    return resp

@auth_bp.context_processor
def inject_user():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return {'current_user': user}
    return {'current_user': None}