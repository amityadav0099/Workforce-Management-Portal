from flask import Blueprint, render_template, session, request
from grievances.models import Grievance
from leaves.models import LeaveRequest
from accounts.decorators import login_required, role_required
from attendance.models import Attendance
from planner.models import CalendarEvent
from sqlalchemy import func
from extensions import db
from datetime import datetime, timedelta
import pytz
import csv
import io
from accounts.models import EmployeeProfile
from flask import Response

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

@reports_bp.route('/break_report')
@login_required
def break_report():
    from planner.models import CalendarEvent
    from datetime import datetime
    
    # Query all events, ordered by date descending
    events = CalendarEvent.query.order_by(CalendarEvent.event_date.desc()).all()
    report_data = []

    for e in events:
        # 1. Get the name from the profile
        if e.user and e.user.profile and e.user.profile.name:
            display_name = e.user.profile.name
        elif e.user:
            display_name = e.user.email
        else:
            display_name = "Unknown User"

        # 2. Calculate duration using your HMS utility
        duration_text = "0h 0m 0s"
        time_range = "N/A"

        if e.time_start and e.time_end:
            # Combine date and time for precise calculation
            start_dt = datetime.combine(e.event_date, e.time_start)
            end_dt = datetime.combine(e.event_date, e.time_end)
            
            # Use your existing utility function
            duration_text = calculate_hms(start_dt, end_dt)
            
            # Format time range with seconds
            time_range = f"{e.time_start.strftime('%I:%M:%S %p')} - {e.time_end.strftime('%I:%M:%S %p')}"

        # 3. Build the report dictionary
        report_data.append({
            "employee": display_name,
            "date": e.event_date.strftime('%d %b, %Y') if e.event_date else "N/A",
            "reason": e.reason.capitalize() if e.reason else "N/A",
            "time": time_range,
            "duration": duration_text
        })

    # Ensure we pass 'report_data' to the template variable 'report'
    return render_template('reports/break_report.html', report=report_data)


@reports_bp.route('/export_payroll_csv')
def export_payroll_csv():
    from accounts.models import EmployeeProfile
    import csv
    import io

    month = request.args.get('month', '02')
    year = request.args.get('year', '2026')
    
    profiles = EmployeeProfile.query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Full Name', 'Mobile', 'Joining Date', 'PAN Number', 
        'Annual CTC', 'Monthly In-Hand', 'Bank Name', 
        'Account Number', 'IFSC Code', 'Status'
    ])
    
    for p in profiles:
        # Safe formatting for CTC and In-Hand to prevent TypeErrors
        safe_ctc = f"{p.ctc:,.2f}" if p.ctc is not None else "0.00"
        safe_in_hand = f"{p.in_hand:,.2f}" if p.in_hand is not None else "0.00"
        
        writer.writerow([
            p.name or "N/A",
            p.mobile or "N/A",
            p.joining_date.strftime('%d-%m-%Y') if p.joining_date else "N/A",
            p.pan_number or "N/A",
            safe_ctc,
            safe_in_hand,
            p.bank_name or "N/A",
            p.account_number or "N/A",
            p.ifsc_code or "N/A",
            p.verification_status or "Pending"
        ])
    
    output.seek(0)
    filename = f"payroll_report_{month}_{year}.csv"
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )