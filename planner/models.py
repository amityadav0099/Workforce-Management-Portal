from extensions import db
from datetime import datetime

class CalendarEvent(db.Model):
    __tablename__ = 'calendar_events'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.String(255), nullable=False) 
    event_date = db.Column(db.Date, nullable=False) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    time_start = db.Column(db.Time, nullable=True) 
    time_end = db.Column(db.Time, nullable=True)

    user = db.relationship('User', backref='events')