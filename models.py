from extensions import db 
from datetime import datetime

class Grievance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default="Open")
    created_by = db.Column(db.String(100))



class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(100))   
    message = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)


    
