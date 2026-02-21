from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from extensions import db
from attendance.models import Attendance
from datetime import datetime, timedelta
import pytz
from accounts.decorators import login_required, role_required

attendance_bp = Blueprint("attendance", __name__, url_prefix="/attendance")

IST = pytz.timezone('Asia/Kolkata')

def calculate_hms(dt_in, dt_out):
    # Force both to be naive to prevent timezone mismatch errors
    naive_in = dt_in.replace(tzinfo=None) if dt_in.tzinfo else dt_in
    naive_out = dt_out.replace(tzinfo=None) if dt_out.tzinfo else dt_out
    
    diff = naive_out - naive_in
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
    
   
    
    # Get location from form
    user_location = request.form.get('location')
    
    # Strict check: If JS failed or was bypassed and no location sent
    if not user_location or user_location in ["GPS_DENIED", "BROWSER_UNSUPPORTED"]:
        flash("Location access is required to clock in.", "rose")
        return redirect(url_for("accounts.dashboard"))
    existing = Attendance.query.filter_by(user_id=user_id, date=today).first()

    if not existing:
        new_entry = Attendance(
            user_id=user_id, 
            date=today,
            clock_in=now_ist, 
            location=user_location # Storing in 'location' column
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
    
    # Get location from form
    user_location_out = request.form.get('location')

    if not user_location_out or user_location_out in ["GPS_DENIED", "BROWSER_UNSUPPORTED"]:
        flash("Location access is required to clock out.", "rose")
        return redirect(url_for("accounts.dashboard"))
    
    if record and not record.clock_out:
        record.clock_out = now_ist
        record.location_out = user_location_out # Storing in 'location_out' column
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
    now_naive = now_ist.replace(tzinfo=None)

    for log in attendance_list:
        if log.clock_in:
            if isinstance(log.clock_in, timedelta):
                dt_in = datetime.combine(log.date, (datetime.min + log.clock_in).time())
            else:
                dt_in = log.clock_in.replace(tzinfo=None) if log.clock_in.tzinfo else log.clock_in
            log.formatted_in = dt_in.strftime('%I:%M:%S %p')
        else:
            dt_in = None
            log.formatted_in = "N/A"

        if log.clock_out:
            if isinstance(log.clock_out, timedelta):
                dt_out = datetime.combine(log.date, (datetime.min + log.clock_out).time())
            else:
                dt_out = log.clock_out.replace(tzinfo=None) if log.clock_out.tzinfo else log.clock_out
            log.formatted_out = dt_out.strftime('%I:%M:%S %p')
        else:
            dt_out = now_naive if log.date == now_ist.date() else None
            log.formatted_out = "Active" if log.date == now_ist.date() else "Missed"

        if dt_in and dt_out:
            log.display_duration = calculate_hms(dt_in, dt_out)
        else:
            log.display_duration = "N/A"

    return render_template('attendance/manage_attendance.html', attendance_list=attendance_list)

@attendance_bp.route('/history')
@login_required
def attendance_history():
    user_id = session.get("user_id")
    logs = Attendance.query.filter_by(user_id=user_id).order_by(Attendance.date.desc()).all()
    now_naive = datetime.now(IST).replace(tzinfo=None)

    for log in logs:
        if log.clock_in:
            if isinstance(log.clock_in, timedelta):
                dt_in = datetime.combine(log.date, (datetime.min + log.clock_in).time())
            else:
                dt_in = log.clock_in.replace(tzinfo=None) if log.clock_in.tzinfo else log.clock_in
            
            if log.clock_out:
                if isinstance(log.clock_out, timedelta):
                    dt_out = datetime.combine(log.date, (datetime.min + log.clock_out).time())
                else:
                    dt_out = log.clock_out.replace(tzinfo=None) if log.clock_out.tzinfo else log.clock_out
            else:
                dt_out = now_naive
            
            log.display_duration = calculate_hms(dt_in, dt_out)
        else:
            log.display_duration = "N/A"

    return render_template('attendance/history.html', logs=logs)