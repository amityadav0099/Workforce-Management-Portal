from extensions import db
from datetime import datetime

class Attendance(db.Model):
    __tablename__ = "attendance"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, default=lambda: datetime.now().date())
    clock_in = db.Column(db.Time, nullable=False)
    clock_out = db.Column(db.Time, nullable=True)
    total_hours = db.Column(db.Float, default=0.0)

    user = db.relationship("User", backref=db.backref("attendance_logs", lazy=True))