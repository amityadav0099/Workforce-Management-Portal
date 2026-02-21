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

# --- REGISTER ALL BLUEPRINTS ---
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
    # Redirects to the logout logic inside the accounts blueprint
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
        # Increase timeout to prevent 'getaddrinfo failed' on Render
        socket.setdefaulttimeout(30) 
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            token = s.dumps(email, salt='password-reset-salt')
            link = url_for('reset_password', token=token, _external=True)
            msg = Message('HR Portal: Password Reset Request', recipients=[email])
            msg.body = f"To reset your password, visit: {link}"
            msg.html = f"<b>HR Portal</b><br><br>Click here: <a href='{link}'>Reset Password</a>"
            try:
                mail.send(msg)
                flash('A reset link has been sent to your email!', 'success')
            except Exception as e:
                # Logs SMTP detail to Render terminal
                print(f"SMTP Error: {str(e)}") 
                flash(f'Error sending email. Check server configuration.', 'danger')
        else:
            flash('Email not found.', 'danger')
        return redirect(url_for('accounts.login'))
    
    # Path explicitly set to folder to avoid TemplateNotFound
    return render_template('accounts/forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=1800)
    except:
        flash('The reset link is invalid or has expired!', 'danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(request.form.get('password'))
            db.session.commit()
            flash('Password updated successfully.', 'success')
            return redirect(url_for('accounts.login'))
    return render_template('accounts/reset_with_new_password.html')

# ================= AGGRESSIVE DATABASE REPAIR =================

@app.route('/fix-db')
def fix_db():
    try:
        # Using a direct connection to bypass ORM sync issues
        with db.engine.connect() as conn:
            # Add missing columns found in your logs
            conn.execute(text("ALTER TABLE grievances ADD COLUMN IF NOT EXISTS hr_comment TEXT"))
            conn.execute(text("ALTER TABLE grievances ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP"))
            
            # Additional safety columns for attendance
            conn.execute(text("ALTER TABLE attendance ADD COLUMN IF NOT EXISTS location_in VARCHAR(255)"))
            conn.execute(text("ALTER TABLE attendance ADD COLUMN IF NOT EXISTS location_out VARCHAR(255)"))
            
            conn.commit()
        return "Database Repair Successful! Missing columns added. ✅"
    except Exception as e:
        return f"Database Repair Failed: {str(e)} ❌"

if __name__ == "__main__":
    # Ensure debug is off for production stability
    app.run(debug=False)