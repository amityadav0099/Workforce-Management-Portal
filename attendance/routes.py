from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from extensions import db
from attendance.models import Attendance
from datetime import datetime
from accounts.decorators import login_required, role_required

attendance_bp = Blueprint("attendance", __name__, url_prefix="/attendance")

@attendance_bp.route("/clock-in", methods=["POST"])
@login_required
def clock_in():
    user_id = session.get("user_id")
    # Using .now().date() to stay consistent with the clock_in timestamp
    today = datetime.now().date()
    
    existing = Attendance.query.filter_by(user_id=user_id, date=today).first()
    
    if not existing:
        user_location = request.form.get('location', 'Location Not Captured')
        
        new_entry = Attendance(
            user_id=user_id, 
            date=today,
            clock_in=datetime.now(),
            location=user_location
        )
        db.session.add(new_entry)
        db.session.commit()
        flash("Clocked in successfully!", "success")
    else:
        flash("You are already clocked in for today.", "rose")
        
    return redirect(url_for("accounts.dashboard"))

@attendance_bp.route("/clock-out", methods=["POST"])
@login_required
def clock_out():
    user_id = session.get("user_id")
    today = datetime.now().date()
    
    record = Attendance.query.filter_by(user_id=user_id, date=today).first()
    
    if record and not record.clock_out:
        record.clock_out = datetime.now()
        db.session.commit()
        flash("Clocked out successfully! Have a great evening.", "success")
    else:
        flash("Clock out failed. You might not have an active shift.", "rose")
        
    return redirect(url_for("accounts.dashboard"))

@attendance_bp.route("/manage")
@login_required
@role_required('hr')
def manage_attendance():
    # Your current query
    attendance_list = Attendance.query.order_by(Attendance.date.desc()).all()
    
    for log in attendance_list:
        if log.clock_in and log.clock_out:
            # Combine the date and time objects into full datetimes for math
            dt_in = datetime.combine(log.date, log.clock_in)
            dt_out = datetime.combine(log.date, log.clock_out)
            
            diff = dt_out - dt_in
            total_seconds = diff.total_seconds()
            
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            
            # Create the custom duration string
            if hours > 0:
                log.display_duration = f"{hours}h {minutes}m"
            else:
                log.display_duration = f"{minutes}m"
        else:
            log.display_duration = "Tracking..."

    return render_template('attendance/manage_attendance.html', 
                           attendance_list=attendance_list, 
                           now=datetime.now())

@attendance_bp.route('/history')
@login_required
def attendance_history():
    user_id = session.get("user_id")
    logs = Attendance.query.filter_by(user_id=user_id).order_by(Attendance.date.desc()).all()
    
    for log in logs:
        if log.clock_in and log.clock_out:
            # Combine the date and time objects to allow subtraction
            dt_in = datetime.combine(log.date, log.clock_in)
            dt_out = datetime.combine(log.date, log.clock_out)
            
            diff = dt_out - dt_in
            total_seconds = diff.total_seconds()
            
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            
            # Create a custom display string
            if hours > 0:
                log.display_duration = f"{hours}h {minutes}m"
            else:
                log.display_duration = f"{minutes}m"
        else:
            log.display_duration = "In Progress"

    return render_template('attendance/history.html', logs=logs)