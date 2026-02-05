from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from .models import LeaveRequest
from models import db
from datetime import datetime



leaves_bp = Blueprint("leaves", __name__, url_prefix="/leaves")


# ================= MAIN LEAVES PAGE =================
@leaves_bp.route("/")
def leave_list():
    if session.get("role") == "employee":
        return redirect(url_for("leaves.apply_leave"))
    elif session.get("role") == "hr":
        return redirect(url_for("leaves.manage_leaves"))
    return redirect(url_for("dashboard"))


# ================= EMPLOYEE APPLY LEAVE =================
@leaves_bp.route("/apply-leave", methods=["GET", "POST"])
def apply_leave():
    if session.get("role") != "employee":
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        from_date = datetime.strptime(
            request.form["from_date"], "%Y-%m-%d"
        ).date()

        to_date = datetime.strptime(
            request.form["to_date"], "%Y-%m-%d"
        ).date()

        leave = LeaveRequest(
            employee=session["username"],
            from_date=from_date,
            to_date=to_date,
            reason=request.form["reason"]
        )

        db.session.add(leave)
        db.session.commit()
        return redirect(url_for("dashboard"))

    return render_template("leaves/apply_leave.html")


# ================= HR MANAGE LEAVES =================
@leaves_bp.route("/manage-leaves")
def manage_leaves():
    if session.get("role") != "hr":
        return redirect(url_for("dashboard"))

    leaves = LeaveRequest.query.all()
    return render_template("leaves/manage_leaves.html", leaves=leaves)




# ================= EMPLOYEE LEAVE STATUS =================
@leaves_bp.route("/my-leaves")
def my_leaves():
    if session.get("role") != "employee":
        return redirect(url_for("dashboard"))

    leaves = LeaveRequest.query.filter_by(
        employee=session["username"]
    ).order_by(LeaveRequest.id.desc()).all()

    return render_template("leaves/my_leaves.html", leaves=leaves)

@leaves_bp.route("/leave-action/<int:id>/<string:action>")
def leave_action(id, action):
    if session.get("role") != "hr":
        return redirect(url_for("dashboard"))

    leave = LeaveRequest.query.get_or_404(id)

    if action == "approve":
        leave.status = "Approved"
        flash("Your leave has been Approved by HR ✅", "success")
    else:
        leave.status = "Rejected"
        flash("Your leave has been Rejected by HR ❌", "danger")

    db.session.commit()
    return redirect(url_for("leaves.manage_leaves"))




