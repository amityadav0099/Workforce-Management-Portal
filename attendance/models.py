from extensions import db
from datetime import datetime
import pytz

# Define IST for the default date value
IST = pytz.timezone('Asia/Kolkata')

class Attendance(db.Model):
    __tablename__ = "attendance"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    # Use a lambda that respects IST for the default date
    date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(IST).date())
    
    # Changed from db.Time to db.DateTime for better math and timezone support
    clock_in = db.Column(db.DateTime, nullable=False)
    clock_out = db.Column(db.DateTime, nullable=True)
    
    total_hours = db.Column(db.Float, default=0.0)
    
    # location stores the Clock-In spot
    location = db.Column(db.String(255)) 
    
    # NEW: Added this column to store the Clock-Out spot
    location_out = db.Column(db.String(255))

    user = db.relationship("User", backref=db.backref("attendance_logs", lazy=True))