from extensions import db
from datetime import datetime

class Grievance(db.Model):
    __tablename__ = "grievances"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    # Category is now safe with a default value
    category = db.Column(db.String(50), nullable=False, default="General") 
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="Open")
    
    # These match the columns we verified in your DB navigator
    hr_comment = db.Column(db.Text)
    resolved_at = db.Column(db.DateTime)
    
    created_by = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Grievance {self.id}>"