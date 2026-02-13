from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import db
from leaves.models import LeaveRequest  # Matches your NOTE
from accounts.decorators import login_required, role_required
from datetime import datetime

leaves_bp = Blueprint("leaves", __name__, url_prefix="/leaves")

# ================= MAIN LEAVES PAGE =================
@leaves_bp.route("/")
@login_required
def leave_list():
    # Automatically direct users based on their assigned role
    if session.get("role") == "hr":
        return redirect(url_for("leaves.manage_leaves"))
    return redirect(url_for("leaves.apply_leave"))

# ================= EMPLOYEE APPLY LEAVE =================
# ================= EMPLOYEE APPLY LEAVE =================
@leaves_bp.route("/apply-leave", methods=["GET", "POST"])
@login_required
@role_required("employee")
def apply_leave():
    if request.method == "POST":
        try:
            # 1. Extract values using the updated HTML 'name' attributes
            raw_start = request.form.get("start_date")
            raw_end = request.form.get("end_date")
            leave_type = request.form.get("leave_type")
            reason = request.form.get("reason")

            # 2. Convert strings to Python date objects
            from_dt = datetime.strptime(raw_start, "%Y-%m-%d").date()
            to_dt = datetime.strptime(raw_end, "%Y-%m-%d").date()

            # 3. BACKEND VALIDATION (The "Binding" Logic)
            today = datetime.now().date()
            
            if from_dt < today:
                flash("Error: Start date cannot be in the past. ❌", "danger")
                return render_template("leaves/apply_leave.html")
            
            if to_dt < from_dt:
                flash("Error: End date cannot be before the start date. ❌", "danger")
                return render_template("leaves/apply_leave.html")

            # 4. Create the database record
            new_leave = LeaveRequest(
                user_id=session["user_id"],
                leave_type=leave_type,
                start_date=from_dt, # Maps to DB column 'start_date'
                end_date=to_dt,     # Maps to DB column 'end_date'
                reason=reason,
                status="Pending"
            )

            db.session.add(new_leave)
            db.session.commit()
            
            flash("Leave application submitted successfully! 🚀", "success")
            return redirect(url_for("leaves.my_leaves"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")

    return render_template("leaves/apply_leave.html")

# ================= EMPLOYEE LEAVE STATUS =================
@leaves_bp.route("/my-leaves")
@login_required
@role_required("employee")
def my_leaves():
    # Employees only see their own history
    leaves = LeaveRequest.query.filter_by(user_id=session["user_id"]).order_by(LeaveRequest.id.desc()).all()
    return render_template("leaves/my_leaves.html", leaves=leaves)

# ================= HR MANAGE LEAVES =================
@leaves_bp.route("/manage-leaves")
@login_required
@role_required("hr")
def manage_leaves():
    # HR views all requests across the company
    all_leaves = LeaveRequest.query.order_by(LeaveRequest.id.desc()).all()
    
    return render_template("leaves/manage_leaves.html", requests=all_leaves)
    


# ================= HR LEAVE ACTION =================
@leaves_bp.route("/leave-action/<int:id>/<string:action>")
@login_required
@role_required("hr")
def leave_action(id, action):
    leave = LeaveRequest.query.get_or_404(id)

    if action.lower() == "approve" or action.lower() == "approved":
        leave.status = "Approved"
        flash(f"Leave approved for request #{id} ✅", "success")
    else:
        leave.status = "Rejected"
        flash(f"Leave rejected for request #{id} ❌", "danger")

    db.session.commit()
    return redirect(url_for("leaves.manage_leaves"))

@leaves_bp.route("/withdraw-leave/<int:id>")
@login_required
@role_required("employee")
def withdraw_leave(id):
    # Ensure the leave exists and belongs to the current user
    leave = LeaveRequest.query.filter_by(id=id, user_id=session["user_id"]).first_or_404()
    
    if leave.status == "Pending":
        db.session.delete(leave)
        db.session.commit()
        flash("Leave request withdrawn successfully.", "success")
    else:
        flash("You cannot withdraw a request that has already been processed.", "danger")
        
    return redirect(url_for("leaves.my_leaves"))