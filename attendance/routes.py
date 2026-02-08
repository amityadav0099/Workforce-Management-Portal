from flask import Blueprint, render_template, redirect, url_for, flash, session
from extensions import db
from attendance.models import Attendance
from datetime import datetime

from accounts.decorators import login_required, role_required

attendance_bp = Blueprint("attendance", __name__, url_prefix="/attendance")

@attendance_bp.route("/clock-in")
def clock_in():
    user_id = session.get("user_id")
    today = datetime.utcnow().date()
    
    # Check if already clocked in today
    existing = Attendance.query.filter_by(user_id=user_id, date=today).first()
    
    if not existing:
        new_entry = Attendance(user_id=user_id, clock_in=datetime.now())
        db.session.add(new_entry)
        db.session.commit()
        flash("Clocked in successfully!", "success")
    else:
        flash("You are already clocked in for today.", "rose")
        
    return redirect(url_for("accounts.dashboard"))

@attendance_bp.route("/clock-out")
def clock_out():
    user_id = session.get("user_id")
    today = datetime.utcnow().date()
    
    record = Attendance.query.filter_by(user_id=user_id, date=today).first()
    
    if record and not record.clock_out:
        record.clock_out = datetime.now()
        db.session.commit()
        flash("Clocked out successfully! Have a great evening.", "success")
    else:
        flash("Clock out failed. Either you haven't clocked in or you already clocked out.", "rose")
        
    return redirect(url_for("accounts.dashboard"))

@attendance_bp.route("/manage")
@login_required
@role_required('hr')
def manage_attendance():
    # Fetch all records, most recent first
    all_attendance = Attendance.query.order_by(Attendance.date.desc(), Attendance.clock_in.desc()).all()
    return render_template("attendance/manage_attendance.html", attendance_list=all_attendance)

@attendance_bp.route('/history')
@login_required
def attendance_history():
    user_id = session.get("user_id")
    # Fetch all logs for the user, newest first
    logs = Attendance.query.filter_by(user_id=user_id).order_by(Attendance.date.desc()).all()
    return render_template('attendance/history.html', logs=logs)