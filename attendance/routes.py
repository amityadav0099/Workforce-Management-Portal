from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from extensions import db
from attendance.models import Attendance
from datetime import datetime
import pytz
from accounts.decorators import login_required, role_required

attendance_bp = Blueprint("attendance", __name__, url_prefix="/attendance")

# Define Timezone (IST)
IST = pytz.timezone('Asia/Kolkata')

def calculate_hms(dt_in, dt_out):
    """Calculates hours, minutes, and seconds between two localized datetimes."""
    diff = dt_out - dt_in
    total_seconds = int(diff.total_seconds())
    
    if total_seconds < 0:
        return "0h 0m 0s"
        
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    return f"{hours}h {minutes}m {seconds}s"

@attendance_bp.route("/clock-in", methods=["POST"])
@login_required
def clock_in():
    user_id = session.get("user_id")
    now_ist = datetime.now(IST)
    today = now_ist.date()
    
    existing = Attendance.query.filter_by(user_id=user_id, date=today).first()
    
    if not existing:
        # Capture the location string from the hidden input in your dashboard form
        user_location = request.form.get('location', 'Location Not Captured')
        
        new_entry = Attendance(
            user_id=user_id, 
            date=today,
            clock_in=now_ist, 
            location=user_location  # Clock-in location
        )
        db.session.add(new_entry)
        db.session.commit()
        flash("Clocked in successfully! 📍", "success")
    else:
        flash("You are already clocked in for today.", "rose")
        
    return redirect(url_for("accounts.dashboard"))

@attendance_bp.route("/clock-out", methods=["POST"])
@login_required
def clock_out():
    user_id = session.get("user_id")
    now_ist = datetime.now(IST)
    today = now_ist.date()
    
    record = Attendance.query.filter_by(user_id=user_id, date=today).first()
    
    if record and not record.clock_out:
        # NEW: Capture the location during clock-out
        user_location_out = request.form.get('location', 'Location Not Captured')
        
        record.clock_out = now_ist
        record.location_out = user_location_out  # Store the logout spot
        db.session.commit()
        flash("Clocked out successfully! 👋", "success")
    else:
        flash("Clock out failed. No active shift found.", "rose")
        
    return redirect(url_for("accounts.dashboard"))

@attendance_bp.route("/manage")
@login_required
@role_required('hr')
def manage_attendance():
    attendance_list = Attendance.query.order_by(Attendance.date.desc()).all()
    now_ist = datetime.now(IST)

    for log in attendance_list:
        if log.clock_in:
            # Ensure we are working with localized datetimes for duration math
            dt_in = log.clock_in
            if dt_in.tzinfo is None:
                dt_in = IST.localize(dt_in)

            if log.clock_out:
                dt_out = log.clock_out
                if dt_out.tzinfo is None:
                    dt_out = IST.localize(dt_out)
            else:
                dt_out = now_ist # Live duration calculation
            
            log.display_duration = calculate_hms(dt_in, dt_out)
            log.is_live = not bool(log.clock_out)
        else:
            log.display_duration = "N/A"

    return render_template('attendance/manage_attendance.html', 
                           attendance_list=attendance_list, 
                           now=now_ist)

@attendance_bp.route('/history')
@login_required
def attendance_history():
    user_id = session.get("user_id")
    logs = Attendance.query.filter_by(user_id=user_id).order_by(Attendance.date.desc()).all()
    now_ist = datetime.now(IST)

    for log in logs:
        if log.clock_in:
            dt_in = log.clock_in
            if dt_in.tzinfo is None:
                dt_in = IST.localize(dt_in)
            
            if log.clock_out:
                dt_out = log.clock_out
                if dt_out.tzinfo is None:
                    dt_out = IST.localize(dt_out)
            else:
                dt_out = now_ist
                
            log.display_duration = calculate_hms(dt_in, dt_out)
        else:
            log.display_duration = "N/A"

    return render_template('attendance/history.html', logs=logs)