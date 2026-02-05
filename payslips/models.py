from models import db
from extensions import db
from datetime import date

class Payslip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee = db.Column(db.String(100))
    month = db.Column(db.String(20))
    salary = db.Column(db.Integer)
    hra = db.Column(db.Integer)
    deductions = db.Column(db.Integer)
    net_salary = db.Column(db.Integer)
    created_on = db.Column(db.Date, default=date.today)