# grievances/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import db
from grievances.models import Grievance
from payslips.models import Notification
from accounts.decorators import login_required, role_required

grievances_bp = Blueprint("grievances", __name__, url_prefix="/grievances")

# ================= VIEW ALL (HR) =================
@grievances_bp.route("/")
@login_required
@role_required("hr")
def list_grievances():
    grievances = Grievance.query.order_by(Grievance.id.desc()).all()
    return render_template("grievances.html", grievances=grievances)

# ================= ADD NEW (Employee) =================
@grievances_bp.route("/add", methods=["GET", "POST"])
@login_required
@role_required("employee")
def add_grievance(): # Renamed to avoid AssertionError
    if request.method == "POST":
        category = request.form.get("category") 
        g = Grievance(
            title=request.form["title"],
            category=category if category else "General",
            description=request.form["description"],
            created_by=session["email"]
        )
        db.session.add(g)
        db.session.commit()
        flash("Grievance submitted successfully", "success")
        return redirect(url_for("accounts.dashboard"))
    return render_template("grievances/add_grievance.html")

# ================= RESOLVE (HR) =================
@grievances_bp.route("/resolve/<int:id>")
@login_required
@role_required("hr")
def resolve(id):
    grievance = Grievance.query.get_or_404(id)
    grievance.status = "Resolved"
    notification = Notification(
        user=grievance.created_by,
        message=f"Your grievance '{grievance.title}' has been resolved."
    )
    db.session.add(notification)
    db.session.commit()
    flash("Grievance marked as resolved", "success")
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