import csv
import io
import pdfkit
from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from extensions import db
from accounts.models import User
from accounts.decorators import login_required, role_required
from payroll.models import PayrollRecord
from datetime import datetime

payroll_bp = Blueprint("payroll", __name__, url_prefix="/payroll")

@payroll_bp.route("/manage")
@login_required
@role_required("hr")
def manage_payroll():
    """Main dashboard with full-year filter."""
    selected_month = request.args.get('month', datetime.now().strftime('%B 2026'))
    # Generates Jan 2026 to Dec 2026
    month_options = [datetime(2026, m, 1).strftime('%B 2026') for m in range(1, 13)]
    payroll_records = PayrollRecord.query.filter_by(month=selected_month).all()
    
    return render_template(
        "payroll/manage.html", 
        payroll_records=payroll_records, 
        selected_month=selected_month,
        month_options=month_options
    )

@payroll_bp.route("/generate/<int:user_id>", methods=["GET", "POST"])
@login_required
@role_required("hr")
def generate_salary(user_id):
    """Handles individual salary review/edit and SAVE logic."""
    user = User.query.get_or_404(user_id)
    # Get current month or the one being processed
    current_month = datetime.now().strftime('%B 2026')
    record = PayrollRecord.query.filter_by(user_id=user_id, month=current_month).first()

    if request.method == "POST":
        # Get data from the form (generate_form.html)
        basic = float(request.form.get('basic_salary', 0))
        allow = float(request.form.get('allowances', 0))
        deduct = float(request.form.get('deductions', 0))
        net = basic + allow - deduct

        if record:
            # Update existing record
            record.basic_salary = basic
            record.allowances = allow
            record.deductions = deduct
            record.net_salary = net
        else:
            # Create new record if it doesn't exist
            record = PayrollRecord(
                user_id=user_id,
                month=current_month,
                basic_salary=basic,
                allowances=allow,
                deductions=deduct,
                net_salary=net,
                status="Processed"
            )
            db.session.add(record)
        
        db.session.commit()
        flash(f"Payroll updated successfully for {user.email}", "success")
        return redirect(url_for('payroll.manage_payroll', month=current_month))
        
    return render_template("payroll/generate_form.html", user=user, record=record)

@payroll_bp.route("/process-all", methods=["POST"])
@login_required
@role_required("hr")
def process_all_salaries():
    employees = User.query.filter_by(role='employee').all()
    target_month = request.form.get('month')

    for emp in employees:
        existing = PayrollRecord.query.filter_by(user_id=emp.id, month=target_month).first()
        if not existing:
            basic, allow = 5000.0, 500.0
            deduct = basic * 0.17
            new_record = PayrollRecord(
                user_id=emp.id, month=target_month,
                basic_salary=basic, allowances=allow,
                deductions=deduct, net_salary=basic + allow - deduct,
                status="Processed"
            )
            db.session.add(new_record)
    
    db.session.commit()
    flash(f"Salaries processed for {target_month}!", "success")
    return redirect(url_for('payroll.manage_payroll', month=target_month))

@payroll_bp.route("/delete/<int:record_id>", methods=["POST"])
@login_required
@role_required("hr")
def delete_payroll(record_id):
    record = PayrollRecord.query.get_or_404(record_id)
    month = record.month
    db.session.delete(record)
    db.session.commit()
    flash("Record deleted.", "success")
    return redirect(url_for('payroll.manage_payroll', month=month))

@payroll_bp.route("/export-csv")
@login_required
@role_required("hr")
def export_payroll_csv():
    selected_month = request.args.get('month')
    records = PayrollRecord.query.filter_by(month=selected_month).all()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Employee', 'Month', 'Base', 'Allowances', 'Deductions', 'Net'])
    for r in records:
        cw.writerow([r.user.email, r.month, r.basic_salary, r.allowances, r.deductions, r.net_salary])
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=Payroll_{selected_month}.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@payroll_bp.route("/download-payslip/<int:record_id>")
@login_required
def download_payslip(record_id):
    record = PayrollRecord.query.get_or_404(record_id)
    html = render_template("payroll/payslip_pdf.html", record=record)

    path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    pdf = pdfkit.from_string(html, False, configuration=config)
    
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=Payslip_{record.user.email}.pdf'
    return response