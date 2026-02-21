from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
from flask_login import login_user, logout_user, current_user
from itsdangerous import URLSafeTimedSerializer
from extensions import db, login_manager, mail
from grievances.models import Grievance
from accounts.models import User
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
from datetime import datetime
import pytz

IST = pytz.timezone('Asia/Kolkata')
current_time_ist = datetime.now(IST)

load_dotenv()

app = Flask(__name__)

# --- DATABASE CONFIGURATION ---
uri = os.getenv("DB_URL") 
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') 

# --- EMAIL CONFIGURATION ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USER')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASS')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# Initialize Extensions
db.init_app(app)
login_manager.init_app(app)
mail.init_app(app)
login_manager.login_view = 'login' # Matches the route below

s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# --- REGISTER BLUEPRINTS ---
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
    return User.query.get(int(user_id))

# ================= AUTHENTICATION ROUTES =================

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for('accounts.dashboard'))
    return redirect(url_for('login'))

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('accounts.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect(url_for('accounts.dashboard'))
        else:
            flash('Invalid email or password', 'danger')
            
    return render_template('accounts/login.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'employee')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'warning')
            return redirect(url_for('register'))
            
        new_user = User(email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
        
    return render_template('accounts/register.html')

@app.route("/logout")
def logout():
    logout_user()
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ================= PASSWORD RECOVERY =================

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        socket.setdefaulttimeout(30) 
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            token = s.dumps(email, salt='password-reset-salt')
            link = url_for('reset_password', token=token, _external=True)
            msg = Message('HR Portal: Password Reset', recipients=[email])
            msg.body = f"To reset your password, visit: {link}"
            try:
                mail.send(msg)
                flash('Reset link sent!', 'success')
            except Exception as e:
                print(f"SMTP Error: {str(e)}")
                flash('Mail server connection failed.', 'danger')
        return redirect(url_for('login'))
    return render_template('accounts/forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=1800)
    except:
        flash('Expired link.', 'danger')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(request.form.get('password'))
            db.session.commit()
            flash('Password updated!', 'success')
            return redirect(url_for('login'))
    return render_template('accounts/reset_with_new_password.html')

# ================= DATABASE MAINTENANCE =================

@app.route('/fix-db')
def fix_db():
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE grievances ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT 'General'"))
            conn.execute(text("ALTER TABLE grievances ADD COLUMN IF NOT EXISTS hr_comment TEXT"))
            conn.execute(text("ALTER TABLE grievances ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP"))
            conn.commit()
        return "Database check complete. ✅"
    except Exception as e:
        return f"Fix failed: {str(e)}"

if __name__ == "__main__":
    app.run(debug=False)