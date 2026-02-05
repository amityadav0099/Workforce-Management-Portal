from models import db
from extensions import db
from datetime import date

class LeaveRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee = db.Column(db.String(100))
    from_date = db.Column(db.Date)
    to_date = db.Column(db.Date)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default="Pending")  
    applied_on = db.Column(db.Date, default=date.today)
