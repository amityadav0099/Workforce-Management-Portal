from extensions import db
from datetime import datetime

class PayrollRecord(db.Model):
    __tablename__ = 'payroll' 

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    month = db.Column(db.String(20), nullable=False) # Ensure this is NOT NULL
    basic_salary = db.Column(db.Float, default=0.0)
    allowances = db.Column(db.Float, default=0.0)
    deductions = db.Column(db.Float, default=0.0)
    net_salary = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default="Pending")
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    user = db.relationship('User', backref=db.backref('payroll_records', lazy=True))

    # ========================================================
    # KEY FIX: Prevents duplicate user + month combinations
    # ========================================================
    __table_args__ = (
        db.UniqueConstraint('user_id', 'month', name='_user_month_uc'),
    )

    def __repr__(self):
        return f"<PayrollRecord {self.user_id} - {self.month}>"