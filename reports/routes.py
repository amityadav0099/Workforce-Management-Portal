from flask import Blueprint, render_template, session, request
from grievances.models import Grievance
from leaves.models import LeaveRequest
from accounts.decorators import login_required, role_required
from attendance.models import Attendance
from sqlalchemy import func
from extensions import db
from datetime import datetime, timedelta
import pytz

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")

IST = pytz.timezone('Asia/Kolkata')

def calculate_hms(dt_in, dt_out):
    """Utility to calculate duration safely between two datetimes."""
    if not dt_in or not dt_out:
        return "N/A"
    
    # Ensure naive comparison to prevent tzinfo errors
    naive_in = dt_in.replace(tzinfo=None) if hasattr(dt_in, 'tzinfo') and dt_in.tzinfo else dt_in
    naive_out = dt_out.replace(tzinfo=None) if hasattr(dt_out, 'tzinfo') and dt_out.tzinfo else dt_out
    
    # Check if either is a timedelta (Residual TIME columns)
    if isinstance(naive_in, timedelta) or isinstance(naive_out, timedelta):
        return "Time Format Error"

    diff = naive_out - naive_in
    total_seconds = int(diff.total_seconds())
    
    if total_seconds < 0:
        return "0h 0m 0s"
        
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"

@reports_bp.route("/")
@login_required
def index():
    g_total = Grievance.query.count()
    l_total = LeaveRequest.query.count()
    
    if session.get("role") == "employee":
        u_id = session.get("user_id")
        my_leaves = LeaveRequest.query.filter_by(user_id=u_id).count()
        return render_template("reports/employee_report.html", leaves=my_leaves)

    return render_template("reports/hr_report.html", g_count=g_total, l_count=l_total)

@reports_bp.route('/attendance-detailed')
@login_required
@role_required('hr')
def attendance_report():
    """Detailed view of every attendance log with formatted times and durations."""
    all_logs = Attendance.query.order_by(Attendance.date.desc()).all()
    now_ist = datetime.now(IST)
    now_naive = now_ist.replace(tzinfo=None)

    for log in all_logs:
        # Format Clock In: Handles residual timedeltas or datetimes
        if log.clock_in:
            if isinstance(log.clock_in, timedelta):
                dt_in = datetime.combine(log.date, (datetime.min + log.clock_in).time())
            else:
                dt_in = log.clock_in.replace(tzinfo=None) if log.clock_in.tzinfo else log.clock_in
            log.formatted_in = dt_in.strftime('%I:%M %p')
        else:
            dt_in = None
            log.formatted_in = "N/A"

        # Format Clock Out
        if log.clock_out:
            if isinstance(log.clock_out, timedelta):
                dt_out = datetime.combine(log.date, (datetime.min + log.clock_out).time())
            else:
                dt_out = log.clock_out.replace(tzinfo=None) if log.clock_out.tzinfo else log.clock_out
            log.formatted_out = dt_out.strftime('%I:%M %p')
        else:
            # Handle Active shifts for the duration timer
            dt_out = now_naive if log.date == now_ist.date() else None
            log.formatted_out = "Active" if dt_out else "Missed"

        # Safe Duration calculation for the template
        if dt_in and dt_out:
            log.display_duration = calculate_hms(dt_in, dt_out)
        else:
            log.display_duration = "N/A"

    return render_template('reports/attendance_detailed.html', logs=all_logs)

@reports_bp.route('/attendance-summary')
@login_required
@role_required('hr')
def attendance_detailed():
    """Summary view grouped by date."""
    report_data = db.session.query(
        Attendance.date, 
        func.count(Attendance.id).label('total_employees')
    ).group_by(Attendance.date).order_by(Attendance.date.desc()).all()

    return render_template('reports/attendance_summary.html', data=report_data)