from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from extensions import db
from accounts.models import User, EmployeeProfile, Task, LeaveRequest
from accounts.decorators import login_required, role_required
from attendance.models import Attendance
from sqlalchemy import func
from extensions import mail
from flask_mail import Message
import secrets
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_login import login_user, logout_user, current_user
import pytz

IST = pytz.timezone('Asia/Kolkata')

accounts_bp = Blueprint("accounts", __name__, url_prefix="/accounts")
UPLOAD_FOLDER = "static/uploads/profile"

@accounts_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash("Email already registered.", "rose")
            return redirect(url_for("accounts.register"))
        new_user = User(email=email, role=role)
        new_user.set_password(password) 
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for("accounts.login"))
    return render_template("accounts/register.html")

@accounts_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if user.role != role:
                flash(f"Unauthorized. You are not registered as {role}.", "rose")
                return redirect(url_for("accounts.login"))
            if not user.is_active:
                flash("This account has been deactivated.", "rose")
                return redirect(url_for("accounts.login"))
            
            # CRITICAL FIX: Establish Flask-Login Session
            login_user(user)
            
            # Keep these for your custom logic if needed
            session["user_id"] = user.id
            session["email"] = user.email
            session["role"] = user.role
            
            flash("Welcome back!", "success")
            return redirect(url_for("accounts.dashboard"))
        else:
            flash("Invalid email or password. Please try again.", "rose")
            return redirect(url_for("accounts.login"))
    return render_template("accounts/login.html")

@accounts_bp.route("/logout")
def logout():
    logout_user() # Clears Flask-Login session
    session.clear() # Clears manual session
    return redirect(url_for("accounts.login"))


# --- USER ROUTES ---

@accounts_bp.route("/dashboard")
@login_required 
def dashboard():
    user_id = session.get("user_id")
    
    # --- 1. Your Existing Time Tracking Logic ---
    active_log = Attendance.query.filter_by(user_id=user_id, clock_out=None).first()
    display_duration = "00:00:00"
    
    if active_log and active_log.clock_in:
        now_ist = datetime.now(IST)
        if active_log.clock_in.tzinfo is None:
            localized_start = IST.localize(active_log.clock_in)
        else:
            localized_start = active_log.clock_in

        duration = now_ist - localized_start
        total_seconds = int(duration.total_seconds())
        if total_seconds < 0: total_seconds = 0
        
        h, remainder = divmod(total_seconds, 3600)
        m, s = divmod(remainder, 60)
        display_duration = f"{h:02}:{m:02}:{s:02}"

    # --- 2. New Dynamic Stats Logic ---
    
    # Get Pending Tasks Count
    pending_count = Task.query.filter_by(user_id=user_id, status='Pending').count()

    # Calculate Leave Balance (Annual Quota of 24 - Approved Leaves)
    annual_quota = 24
    used_leaves = db.session.query(func.sum(LeaveRequest.days_requested)).filter(
        LeaveRequest.user_id == user_id,
        LeaveRequest.status == 'Approved'
    ).scalar() or 0
    leave_balance = annual_quota - used_leaves

    return render_template(
        "accounts/dashboard.html", 
        active_log=active_log, 
        display_duration=display_duration,
        pending_count=pending_count,
        leave_balance=leave_balance
    )

@accounts_bp.route('/clock-in', methods=['POST'])
@login_required
def clock_in():
    user_id = session.get("user_id")
    today = datetime.now().date()
    
    # Safety check: Prevent double clock-in
    existing = Attendance.query.filter_by(user_id=user_id, date=today, clock_out=None).first()
    if not existing:
        new_log = Attendance(
            user_id=user_id,
            date=today,
            clock_in=datetime.now().time()
        )
        db.session.add(new_log)
        db.session.commit()
        flash("Shift started! Have a productive day.", "success")
    return redirect(url_for('accounts.dashboard'))

@accounts_bp.route('/clock-out', methods=['POST'])
@login_required
def clock_out():
    user_id = session.get("user_id")
    today = datetime.now().date()
    
    log = Attendance.query.filter_by(user_id=user_id, date=today, clock_out=None).first()
    if log:
        log.clock_out = datetime.now().time()
        
        # Calculate Total Hours (Decimal)
        start_dt = datetime.combine(today, log.clock_in)
        end_dt = datetime.combine(today, log.clock_out)
        duration = end_dt - start_dt
        log.total_hours = round(duration.total_seconds() / 3600, 2)
        
        db.session.commit()
        flash("Shift ended successfully.", "info")
    return redirect(url_for('accounts.dashboard'))

@accounts_bp.route("/my-profile", methods=["GET", "POST"])
@login_required
def my_profile():
    user_id = session.get("user_id")
    user = User.query.get(user_id)
    if not user:
        session.clear()
        return redirect(url_for("accounts.login")) 

    profile = EmployeeProfile.query.filter_by(user_id=user.id).first()

    if request.method == "POST":
        if not profile:
            profile = EmployeeProfile(user_id=user.id)
            db.session.add(profile)

        # 1. Basic Information
        profile.name = request.form.get("name")
        profile.gender = request.form.get("gender")
        profile.mobile = request.form.get("mobile")
        profile.email = user.email # Keeps it synced with account
        
        # 2. Location Information
        profile.address = request.form.get("address")
        profile.city = request.form.get("city")
        profile.state = request.form.get("state")
        
        # 3. Professional Details
        profile.pan_number = request.form.get("pan_number")
        
        # 4. Banking Details
        profile.ifsc_code = request.form.get("ifsc_code")
        profile.bank_name = request.form.get("bank_name")
        profile.branch_name = request.form.get("branch_name")
        profile.account_number = request.form.get("account_number")
        profile.account_holder = request.form.get("account_holder")

        # 5. Date Handling
        dob = request.form.get("dob")
        doj = request.form.get("joining_date")
        try:
            if dob: profile.dob = datetime.strptime(dob, "%Y-%m-%d").date()
            if doj: profile.joining_date = datetime.strptime(doj, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD.", "rose")

        # 6. Comprehensive File Upload Handling
        full_path = os.path.join(current_app.root_path, UPLOAD_FOLDER)
        os.makedirs(full_path, exist_ok=True)
        
        files_to_upload = [
            "profile_photo", "pan_photo", "aadhar_photo", 
            "bank_statement", "passbook_photo", "cancelled_cheque"
        ]

        for file_key in files_to_upload:
            file = request.files.get(file_key)
            if file and file.filename != '':
                ext = file.filename.rsplit('.', 1)[1].lower()
                # Generates names like: user1_profile_photo.jpg
                filename = secure_filename(f"user{user.id}_{file_key}.{ext}")
                file.save(os.path.join(full_path, filename))
                setattr(profile, file_key, filename)

        db.session.commit()
        flash("Profile and all documents updated successfully", "success")
        return redirect(url_for("accounts.my_profile"))

    return render_template("accounts/my_profile.html", profile=profile)

# --- HR MANAGEMENT & VERIFICATION ROUTES ---

@accounts_bp.route('/hr/employees')
@login_required
@role_required('hr')
def employee_list():
    all_users = User.query.all()
    return render_template('accounts/employee_list.html', users=all_users)

@accounts_bp.route('/hr/verifications')
@login_required
@role_required('hr')
def pending_verifications():
    pending = EmployeeProfile.query.filter(EmployeeProfile.verification_status != 'Verified').all()
    return render_template('accounts/hr_verify_list.html', profiles=pending)

@accounts_bp.route('/hr/verify/<int:profile_id>/<status>')
@login_required
@role_required('hr')
def update_verification(profile_id, status):
    profile = EmployeeProfile.query.get_or_404(profile_id)
    if status in ['Verified', 'Rejected']:
        profile.verification_status = status
        db.session.commit()
        flash(f"Profile for {profile.name} marked as {status}.", "success")
    return redirect(url_for('accounts.pending_verifications'))

@accounts_bp.route('/hr/toggle-user/<int:user_id>')
@login_required
@role_required('hr')
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active  
    db.session.commit()
    status = "activated" if user.is_active else "deactivated"
    flash(f"User {user.email} has been {status}.", "success")
    return redirect(url_for('accounts.employee_list'))

@accounts_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate a temporary token (or use your User model's token method)
            token = secrets.token_hex(16) 
            # Ideally, save this token to your User model with an expiry time
            
            msg = Message('Password Reset Request - T3X Connect',
                          recipients=[email])
            
            # Using _external=True to generate an absolute URL (http://...)
            reset_url = url_for('accounts.reset_token', token=token, _external=True)
            
            msg.body = f"To reset your password, visit the following link: {reset_url}"
            
            try:
                mail.send(msg)
                flash("An email has been sent with instructions to reset your password.", "info")
            except Exception as e:
                print(f"Mail Error: {e}")
                flash("Error sending email. Please contact support.", "rose")
        else:
            flash("If that email exists in our system, a reset link has been sent.", "info")
            
        return redirect(url_for("accounts.login"))
        
    # Corrected template path to match your folder structure
    return render_template("accounts/forgot_password.html")

@accounts_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_token(token):
    # Logic to verify token and update password goes here
    return render_template("accounts/reset_password.html", token=token)