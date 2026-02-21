from extensions import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# =========================
# USER / AUTH MODEL
# =========================
class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False) # admin, employee, hr
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)

    profile = db.relationship(
        "EmployeeProfile",
        backref="user",
        uselist=False,
        cascade="all, delete"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"

# =========================
# EMPLOYEE PROFILE MODEL
# =========================
class EmployeeProfile(db.Model):
    __tablename__ = "employee_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        unique=True
    )

    # --- Personal Details ---
    name = db.Column(db.String(100))
    gender = db.Column(db.String(10)) # Added: Male, Female, Other
    dob = db.Column(db.Date)
    mobile = db.Column(db.String(15))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    state = db.Column(db.String(50)) # Fixed: lowercase 'state'
    
    # --- Professional & Salary ---
    joining_date = db.Column(db.Date)
    pan_number = db.Column(db.String(20)) # Added: For storing the ID string
    ctc = db.Column(db.Float, default=0.0) # Added: Annual CTC
    in_hand = db.Column(db.Float, default=0.0) # Added: Monthly In-hand

    # --- Banking Details ---
    account_holder = db.Column(db.String(100))
    bank_name = db.Column(db.String(100))
    branch_name = db.Column(db.String(100))
    account_number = db.Column(db.String(30))
    ifsc_code = db.Column(db.String(20))

    # --- Document Filenames (Storage paths) ---
    profile_photo = db.Column(db.String(200))
    pan_photo = db.Column(db.String(200))
    aadhar_photo = db.Column(db.String(200))
    bank_statement = db.Column(db.String(200)) # Added
    passbook_photo = db.Column(db.String(200)) # Added
    cancelled_cheque = db.Column(db.String(200)) # Added

    # --- Verification System ---
    verification_status = db.Column(db.String(20), default="Pending")
    hr_remarks = db.Column(db.Text)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<EmployeeProfile user_id={self.user_id}>"
    
    def __getitem__(self, key):
        return getattr(self, key)
    
# accounts/models.py

# ... keep your User and EmployeeProfile classes as they are ...

# =========================
# TASK MODEL
# =========================
class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default="Pending") # Pending, Completed
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Task {self.title} - {self.status}>"

# =========================
# LEAVE REQUEST MODEL
# =========================
class LeaveRequest(db.Model):
    __tablename__ = "leave_requests"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    days_requested = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default="Approved") # Pending, Approved, Rejected
    reason = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)