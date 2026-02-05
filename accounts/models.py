from extensions import db
from datetime import datetime

class EmployeeProfile(db.Model):
    __tablename__ = "employee_profiles"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)

    # Basic details
    name = db.Column(db.String(100))
    mobile = db.Column(db.String(15))
    email = db.Column(db.String(120))
    dob = db.Column(db.Date)
    joining_date = db.Column(db.Date)
    address = db.Column(db.Text)

    pan = db.Column(db.String(20))
    aadhar = db.Column(db.String(20))

    # Bank details
    account_number = db.Column(db.String(30))
    ifsc_code = db.Column(db.String(20))
    bank_name = db.Column(db.String(50))
    branch_name = db.Column(db.String(50))
    account_holder = db.Column(db.String(100))

    # Uploads (sirf file path save hoga)
    profile_photo = db.Column(db.String(200))
    pan_photo = db.Column(db.String(200))
    aadhar_photo = db.Column(db.String(200))

    bank_statement = db.Column(db.String(200))
    cancelled_cheque = db.Column(db.String(200))
    passbook = db.Column(db.String(200))

    created_on = db.Column(db.DateTime, default=datetime.utcnow)

