from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from payslips.models import Payslip # We store results in the payslip table
from accounts.models import User
from accounts.decorators import login_required, role_required
from payroll.models import PayrollRecord

# Create the blueprint
payroll_bp = Blueprint("payroll", __name__, url_prefix="/payroll")

@payroll_bp.route("/manage")
@login_required
@role_required("hr")
def manage_payroll():
    # Fetch all employees to show in the payroll dashboard
    employees = User.query.filter_by(role='employee').all()

    all_records = PayrollRecord.query.all()
    return render_template("payroll/manage.html", employees=employees)

@payroll_bp.route("/generate/<int:user_id>", methods=["GET", "POST"])
@login_required
@role_required("hr")
def generate_salary(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == "POST":
        basic = float(request.form.get("basic_salary", 0))
        allowances = float(request.form.get("allowances", 0))
        
        # ✅ Automated Deduction Logic
        pf_deduction = basic * 0.12  # 12% PF
        tax_deduction = basic * 0.05  # 5% TDS
        total_deductions = pf_deduction + tax_deduction
        
        # Calculate Final Net Salary
        net = basic + allowances - total_deductions

        new_slip = Payslip(
            user_id=user.id,
            month=request.form.get("month"),
            basic_salary=basic,
            allowances=allowances,
            deductions=total_deductions,
            net_salary=net
        )
        db.session.add(new_slip)
        db.session.commit()
        
        flash(f"Salary processed for {user.email}. Net: ₹{net:,.2f}", "success")
        return redirect(url_for('payroll.manage_payroll'))
        
    return render_template("payroll/generate_form.html", user=user)