from app import create_app, db

app = create_app()

@app.route('/')
def index():
    from flask import redirect, url_for, session
    if 'user_id' in session:
        if session['role'] == 'manager':
            return redirect(url_for('manager.dashboard'))
        elif session['role'] == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('employee.dashboard'))
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    app.run(debug=True, port=10101)