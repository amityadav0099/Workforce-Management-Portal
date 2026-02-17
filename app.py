from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from extensions import db
from grievances.models import Grievance
from payslips.models import Notification
from accounts.models import User, EmployeeProfile
from attendance.models import Attendance
from payroll.models import PayrollRecord
from accounts.decorators import login_required
from datetime import datetime
from attendance.routes import attendance_bp
import os
import socket
from dotenv import load_dotenv

load_dotenv()

# Blueprint Imports
from payslips.routes import payslips_bp
from payroll.routes import payroll_bp
from leaves.routes import leaves_bp
from accounts.routes import accounts_bp
from grievances.routes import grievances_bp
from reports.routes import reports_bp

app = Flask(__name__)

# --- CONFIGURATION (THE POSTGRES FIX) ---
# Pull the URL from Render's environment variable
uri = os.getenv("DB_URL") 

# MANDATORY FIX: SQLAlchemy requires 'postgresql://', but Render gives 'postgres://'
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') 

# --- EMAIL CONFIGURATION ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USER') 
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASS') # Use MAIL_PASS here
mail = Mail(app)

s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
db.init_app(app)

# --- AUTOMATIC TABLE CREATION FIX ---
# This is now outside the "if __name__" block so it runs on Render
with app.app_context():
    db.create_all()

# --- REGISTER BLUEPRINTS ---
app.register_blueprint(leaves_bp)
app.register_blueprint(payslips_bp)
app.register_blueprint(accounts_bp) 
app.register_blueprint(grievances_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(payroll_bp)
app.register_blueprint(attendance_bp)

# ================= ROOT REDIRECTS =================

@app.route("/")
def index():
    if 'user_id' in session:
        return redirect(url_for('accounts.dashboard'))
    return redirect(url_for('accounts.login'))

@app.route("/login")
def login_redirect():
    return redirect(url_for('accounts.login'))

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
        socket.setdefaulttimeout(15)
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            token = s.dumps(email, salt='password-reset-salt')
            link = url_for('reset_password', token=token, _external=True)
            msg = Message('HR Portal: Password Reset Request', 
                          sender=app.config['MAIL_USERNAME'], 
                          recipients=[email])
            msg.html = f"Click here to reset: <a href='{link}'>Reset Password</a>"
            try:
                mail.send(msg)
                flash('A reset link has been sent to your Gmail!', 'success')
            except Exception as e:
                flash(f'Mail error: {str(e)}', 'danger')
        return redirect(url_for('accounts.login'))
    return render_template('forgot_password.html')

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
    return render_template('reset_with_new_password.html')

# ================= APP STARTUP =================

@app.route('/fix-db')
def fix_db():
    try:
        from sqlalchemy import text
        # This command adds the missing column to your PostgreSQL DB on Render
        
        db.session.execute(text("ALTER TABLE attendance ADD COLUMN IF NOT EXISTS location_in VARCHAR(255)"))
        db.session.execute(text("ALTER TABLE attendance ADD COLUMN IF NOT EXISTS location_out VARCHAR(255)"))
        db.session.commit()
        return "Database updated successfully! ✅"
    except Exception as e:
        return f"Error updating database: {str(e)} ❌"

if __name__ == "__main__":
    # Local development only
    app.run(debug=True)