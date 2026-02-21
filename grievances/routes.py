# grievances/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import db
from grievances.models import Grievance
from payslips.models import Notification
from accounts.decorators import  role_required
from flask_login import current_user, login_required
from datetime import datetime
import pytz


IST = pytz.timezone('Asia/Kolkata')

grievances_bp = Blueprint("grievances", __name__, url_prefix="/grievances")

# ================= VIEW ALL (HR) =================
@grievances_bp.route("/")
@login_required
@role_required("hr")
def list_grievances():
    status_filter = request.args.get('status')
    query = Grievance.query
    if status_filter:
        query = query.filter_by(status=status_filter)

    total_count = Grievance.query.count()
    pending_count = Grievance.query.filter_by(status='Open').count()
    resolved_count = Grievance.query.filter_by(status='Resolved').count()
    grievances = query.order_by(Grievance.id.desc()).all()
    
    return render_template("grievances/grievances.html", grievances=grievances, total_count=total_count, pending_count=pending_count, resolved_count=resolved_count)

# ================= ADD NEW (Employee) =================
@grievances_bp.route("/add", methods=["GET", "POST"])
@login_required
@role_required("employee")
def add_grievance():
    if request.method == "POST":
        category = request.form.get("category") 
        g = Grievance(
            title=request.form["title"],
            category=category if category else "General",
            description=request.form["description"],
            created_by=current_user.email # Use current_user
        )
        db.session.add(g)
        db.session.commit()
        flash("Grievance submitted successfully", "success")
        return redirect(url_for("accounts.dashboard"))
    return render_template("grievances/add_grievance.html")

# ================= RESOLVE (HR) =================
@grievances_bp.route("/resolve/<int:id>",methods=["POST"])
@login_required
@role_required("hr")
def resolve(id):
    grievance = Grievance.query.get_or_404(id)
    
    # Get values from the modal form
    new_status = request.form.get('status') # This will be 'Resolved' or 'Rejected'
    comment = request.form.get('hr_comment')
    
    # Update the grievance record
    grievance.status = new_status
    grievance.hr_comment = comment
    grievance.resolved_at = datetime.now(IST)
    
    # Create notification with the new status
    notification = Notification(
        user=grievance.created_by,
        message=f"Your grievance '{grievance.title}' has been {new_status.lower()} with HR feedback."
    )
    
    db.session.add(notification)
    db.session.commit()
    
    flash(f"Grievance marked as {new_status}", "success")
    return redirect(url_for("grievances.list_grievances"))

@grievances_bp.route("/delete/<int:id>")
@login_required
@role_required("hr")
def delete_grievance(id):
    grievance = Grievance.query.get_or_404(id)
    db.session.delete(grievance)
    db.session.commit()
    flash("Grievance deleted successfully", "success")
    return redirect(url_for("dashboard"))




# grievances/routes.py



# ================= EMPLOYEE VIEW =================
@grievances_bp.route("/my-requests")
@login_required
@role_required("employee")
def my_requests():
    my_grievances = Grievance.query.filter_by(created_by=current_user.email).order_by(Grievance.id.desc()).all()
    return render_template("grievances/my_request.html", my_grievances=my_grievances)