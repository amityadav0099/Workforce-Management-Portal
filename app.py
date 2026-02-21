from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from extensions import db, login_manager, mail
from grievances.models import Grievance
from payslips.models import Notification
from accounts.models import User, EmployeeProfile
from attendance.models import Attendance
from payroll.models import PayrollRecord
from accounts.decorators import login_required
from datetime import datetime
import os
import socket
from sqlalchemy import text
from dotenv import load_dotenv

# Blueprint Imports
from payslips.routes import payslips_bp
from payroll.routes import payroll_bp
from leaves.routes import leaves_bp
from accounts.routes import accounts_bp
from grievances.routes import grievances_bp
from reports.routes import reports_bp
from attendance.routes import attendance_bp
from planner.routes import planner_bp

load_dotenv()

app = Flask(__name__)

# --- DATABASE CONFIGURATION ---
uri = os.getenv("DB_URL") 
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') 

# --- EMAIL CONFIGURATION (Using hr@tricorniotec.com) ---
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 465))
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'True') == 'True'
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'False') == 'True'
app.config['MAIL_USERNAME'] = 'hr@tricorniotec.com' 
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASS')
app.config['MAIL_DEFAULT_SENDER'] = 'hr@tricorniotec.com'

# Initialize Extensions
db.init_app(app)
login_manager.init_app(app)
mail.init_app(app)
login_manager.login_view = 'accounts.login'

s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# --- REGISTER ALL 8 BLUEPRINTS ---
app.register_blueprint(leaves_bp)
app.register_blueprint(payslips_bp)
app.register_blueprint(accounts_bp) 
app.register_blueprint(grievances_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(payroll_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(planner_bp)

@login_manager.user_loader
def load_user(user_id):
    from accounts.models import User
    return User.query.get(int(user_id))

# ================= ROOT REDIRECTS =================

@app.route("/")
def index():
    if 'user_id' in session:
        return redirect(url_for('accounts.dashboard'))
    return redirect(url_for('accounts.login'))

@app.route("/login")
def login_redirect():
    return redirect(url_for('accounts.login'))

@app.route("/logout")
def logout_redirect():
    return redirect(url_for('accounts.logout'))

@app.route("/register")
def register_redirect():
    return redirect(url_for('accounts.register'))

@app.route("/dashboard")
def dashboard_redirect():
    return redirect(url_for('accounts.dashboard'))

# ================= PASSWORD RECOVERY =================

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        # Extend timeout for Render's networking to prevent getaddrinfo failures
        socket.setdefaulttimeout(30) 
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            token = s.dumps(email, salt='password-reset-salt')
            link = url_for('reset_password', token=token, _external=True)
            msg = Message('Workforce Portal: Password Reset', recipients=[email])
            msg.body = f"Reset your password by visiting: {link}"
            msg.html = f"<p>Please use this link to reset your password: <a href='{link}'>Reset Password</a></p>"
            try:
                mail.send(msg)
                flash('A reset link has been sent to your email!', 'success')
            except Exception as e:
                print(f"SMTP Error: {str(e)}") 
                flash(f'Error sending email. Please check server settings.', 'danger')
        else:
            flash('Email not found.', 'danger')
        return redirect(url_for('accounts.login'))
    
    return render_template('accounts/forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=1800)
    except:
        flash('Expired or invalid reset link.', 'danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(request.form.get('password'))
            db.session.commit()
            flash('Password updated successfully!', 'success')
            return redirect(url_for('accounts.login'))
    return render_template('accounts/reset_with_new_password.html')

# ================= CRITICAL DATABASE REPAIR =================

@app.route('/fix-db')
def fix_db():
    try:
        # Using a raw connection to ensure ALTER commands are committed to Render Postgres
        with db.engine.connect() as conn:
            # Fixes for 'grievances' table
            conn.execute(text("ALTER TABLE grievances ADD COLUMN IF NOT EXISTS hr_comment TEXT"))
            conn.execute(text("ALTER TABLE grievances ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP"))
            
            # Fixes for 'attendance' table
            conn.execute(text("ALTER TABLE attendance ADD COLUMN IF NOT EXISTS location_in VARCHAR(255)"))
            conn.execute(text("ALTER TABLE attendance ADD COLUMN IF NOT EXISTS location_out VARCHAR(255)"))
            
            conn.commit()
        return "Database Repair Successful! All missing columns injected. ✅"
    except Exception as e:
        return f"Database Repair Failed: {str(e)} ❌"

if __name__ == "__main__":
    app.run(debug=False)