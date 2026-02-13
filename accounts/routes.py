from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from datetime import datetime
from extensions import db
from accounts.models import User, EmployeeProfile
from accounts.decorators import login_required, role_required
from attendance.models import Attendance
import os
from werkzeug.utils import secure_filename

# Blueprint definition
accounts_bp = Blueprint("accounts", __name__, url_prefix="/accounts")

UPLOAD_FOLDER = "static/uploads/profile"

# --- AUTHENTICATION ROUTES ---

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
    session.clear() 
    return redirect(url_for("accounts.login"))

# --- USER ROUTES ---

@accounts_bp.route('/dashboard')
@login_required 
def dashboard():
    user_id = session.get("user_id")
    # Use local time for attendance tracking rather than UTC to avoid date-shift issues
    today = datetime.now().date() 

    # Look for a record for today where the user has NOT yet clocked out
    active_log = Attendance.query.filter_by(
        user_id=user_id, 
        date=today, 
        clock_out=None
    ).first()

    return render_template(
        'accounts/dashboard.html', 
        role=session.get('role'),
        user_name=session.get('email'),
        active_log=active_log  # This powers the button toggle in your HTML
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