from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from extensions import db
from attendance.models import Attendance
from datetime import datetime, timedelta
import pytz
import requests
from accounts.decorators import login_required, role_required

attendance_bp = Blueprint("attendance", __name__, url_prefix="/attendance")

IST = pytz.timezone('Asia/Kolkata')

def get_readable_address(coords_str):
    """
    Converts 'Lat: 28.123, Lon: 77.123' into a real street address.
    """
    if not coords_str or "Lat:" not in coords_str:
        return "Location N/A"
    
    try:
        # Extract coordinates from string format "Lat: X, Lon: Y"
        parts = coords_str.replace("Lat:", "").replace("Lon:", "").split(",")
        lat = parts[0].strip()
        lon = parts[1].strip()

        # Reverse Geocoding via Nominatim (OpenStreetMap)
        headers = {'User-Agent': 'HR_Portal_App_v1'}
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        
        return data.get('display_name', coords_str)
    except Exception as e:
        print(f"Geocoding error: {e}")
        return coords_str

def calculate_hms(dt_in, dt_out):
    if not dt_in or not dt_out:
        return "N/A"
    
    # Standardize to naive for subtraction
    naive_in = dt_in.replace(tzinfo=None) if hasattr(dt_in, 'tzinfo') and dt_in.tzinfo else dt_in
    naive_out = dt_out.replace(tzinfo=None) if hasattr(dt_out, 'tzinfo') and dt_out.tzinfo else dt_out
    
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
    
    raw_location = request.form.get('location')
    
    if not raw_location or raw_location in ["GPS_DENIED", "BROWSER_UNSUPPORTED"]:
        flash("Location access is required to clock in.", "rose")
        return redirect(url_for("accounts.dashboard"))

    readable_location = get_readable_address(raw_location)

    existing = Attendance.query.filter_by(user_id=user_id, date=today).first()

    if not existing:
        new_entry = Attendance(
            user_id=user_id, 
            date=today,
            clock_in=now_ist, 
            location=readable_location 
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
    raw_location_out = request.form.get('location')

    if not raw_location_out or raw_location_out in ["GPS_DENIED", "BROWSER_UNSUPPORTED"]:
        flash("Location access is required to clock out.", "rose")
        return redirect(url_for("accounts.dashboard"))
    
    readable_location_out = get_readable_address(raw_location_out)

    if record and not record.clock_out:
        record.clock_out = now_ist
        record.location_out = readable_location_out
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
    now_ist = datetime.now(IST).replace(tzinfo=None)

    for log in attendance_list:
        def process_time(val, log_date):
            if isinstance(val, timedelta):
                return datetime.combine(log_date, (datetime.min + val).time())
            return val.replace(tzinfo=None) if val and hasattr(val, 'tzinfo') and val.tzinfo else val

        dt_in = process_time(log.clock_in, log.date)
        dt_out = process_time(log.clock_out, log.date) if log.clock_out else (now_ist if log.date == now_ist.date() else None)

        log.formatted_in = dt_in.strftime('%I:%M:%S %p') if dt_in else "N/A"
        
        if log.clock_out:
            log.formatted_out = dt_out.strftime('%I:%M:%S %p')
        else:
            log.formatted_out = "Active" if log.date == now_ist.date() else "Missed"

        log.display_duration = calculate_hms(dt_in, dt_out)

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
                dt_in = log.clock_in.replace(tzinfo=None) if hasattr(log.clock_in, 'tzinfo') and log.clock_in.tzinfo else log.clock_in
            
            if log.clock_out:
                if isinstance(log.clock_out, timedelta):
                    dt_out = datetime.combine(log.date, (datetime.min + log.clock_out).time())
                else:
                    dt_out = log.clock_out.replace(tzinfo=None) if hasattr(log.clock_out, 'tzinfo') and log.clock_out.tzinfo else log.clock_out
            else:
                dt_out = now_naive if log.date == now_naive.date() else None
            
            log.display_duration = calculate_hms(dt_in, dt_out)
        else:
            log.display_duration = "N/A"

    return render_template('attendance/history.html', logs=logs)