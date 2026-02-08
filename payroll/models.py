from extensions import db
from datetime import datetime

class PayrollRecord(db.Model):
    # 1. Match the table name seen in your MySQL Workbench
    __tablename__ = 'payroll' 

    id = db.Column(db.Integer, primary_key=True)
    
    # 2. MATCH YOUR USER MODEL: Change 'user.id' to 'users.id'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # 3. Match the actual column names from your database screenshot
    month = db.Column(db.String(20))
    basic_salary = db.Column(db.Float, default=0.0) # Matches 'basic_salary' in MySQL
    allowances = db.Column(db.Float, default=0.0)
    deductions = db.Column(db.Float, default=0.0)
    net_salary = db.Column(db.Float, default=0.0)   # Matches 'net_salary' in MySQL
    status = db.Column(db.String(20), default="Pending")
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to get user data in the template
    user = db.relationship('User', backref=db.backref('payroll_records', lazy=True))