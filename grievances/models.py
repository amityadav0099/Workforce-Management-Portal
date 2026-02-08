from extensions import db
from datetime import datetime

class Grievance(db.Model):
    __tablename__ = "grievances"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    # --- ADD THIS LINE ---
    category = db.Column(db.String(50), nullable=False, default="General") 
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="Open")
    created_by = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Grievance {self.id}>"
    

