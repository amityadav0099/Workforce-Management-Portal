from flask import Blueprint, render_template, session
from grievances.models import Grievance
from leaves.models import LeaveRequest
from accounts.decorators import login_required

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")

@reports_bp.route("/")
@login_required
def index():
    # Fixes the property error by using standard queries
    g_total = Grievance.query.count()
    l_total = LeaveRequest.query.count()
    
    if session.get("role") == "employee":
        # Use user_id instead of 'employee' to match your DB
        u_id = session.get("user_id")
        my_leaves = LeaveRequest.query.filter_by(user_id=u_id).count()
        return render_template("reports/employee_report.html", leaves=my_leaves)

    return render_template("reports/hr_report.html", g_count=g_total, l_count=l_total)