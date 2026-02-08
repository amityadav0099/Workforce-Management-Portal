from extensions import db
from datetime import date, datetime


# =========================
# PAYSLIP MODEL
# =========================
class Payslip(db.Model):
    __tablename__ = "payslips"

    id = db.Column(db.Integer, primary_key=True)
    # Changed 'employee' string to 'employee_email' to avoid conflict with relationship
    employee_email = db.Column(db.String(120)) 
    month = db.Column(db.String(20))

    # Rename these to match the 'basic_salary' your error is looking for
    basic_salary = db.Column(db.Integer) 
    hra = db.Column(db.Integer)
    deductions = db.Column(db.Integer)
    net_salary = db.Column(db.Integer)
    
    # Ensure this matches your MySQL table 'users' or 'user'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    created_on = db.Column(db.Date, default=date.today)

    # This relationship is now unique and won't crash
    user = db.relationship('User', backref='payslips_list')

    def __repr__(self):
        return f"<Payslip {self.employee_email} {self.month}>"


# =========================
# NOTIFICATION MODEL
# =========================
class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(120))      # email of user
    message = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)

    created_on = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Notification {self.id}>"
