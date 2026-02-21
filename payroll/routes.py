import csv
import io
import pandas as pd
import pdfkit
import platform
from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, current_app
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
    
    # Get all employees to show in the list
    employees = User.query.filter_by(role='employee').all()
    
    # Get all records for this month to check against the employee list
    payroll_records = PayrollRecord.query.filter_by(month=selected_month).all()
    
    month_options = [datetime(2026, m, 1).strftime('%B 2026') for m in range(1, 13)]
    
    return render_template(
        "payroll/manage.html", 
        employees=employees, # Added this
        payroll_records=payroll_records, 
        selected_month=selected_month,
        month_options=month_options
    )

@payroll_bp.route("/generate/<int:user_id>", methods=["GET", "POST"])
@login_required
@role_required("hr")
def generate_salary(user_id):
    user = User.query.get_or_404(user_id)
    current_month = datetime.now().strftime('%B 2026')
    record = PayrollRecord.query.filter_by(user_id=user_id, month=current_month).first()

    if request.method == "POST":
        basic = float(request.form.get('basic_salary', 0))
        allow = float(request.form.get('allowances', 0))
        deduct = float(request.form.get('deductions', 0))
        net = basic + allow - deduct

        if record:
            # Update existing instead of creating new
            record.basic_salary = basic
            record.allowances = allow
            record.deductions = deduct
            record.net_salary = net
            flash(f"Updated existing slip for {user.email}", "info")
        else:
            # Create new only if it doesn't exist
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
            flash(f"New slip generated for {user.email}", "success")
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash("Database error: Duplicate entry prevented.", "danger")
            
        return redirect(url_for('payroll.manage_payroll', month=current_month))
        
    return render_template("payroll/generate_form.html", user=user, record=record)

@payroll_bp.route("/process-all", methods=["POST"])
@login_required
@role_required("hr")
def process_all_salaries():
    employees = User.query.filter_by(role='employee').all()
    target_month = request.form.get('month')

    skipped = 0
    added = 0

    for emp in employees:
        # Strict check before adding
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
            added += 1
        else:
            skipped += 1
    
    db.session.commit()
    flash(f"Processed: {added} | Skipped Duplicates: {skipped} for {target_month}", "success")
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

@payroll_bp.route('/import-payroll', methods=['POST'])
@login_required
@role_required("hr")
def import_payroll():
    file = request.files.get('file')
    if not file or file.filename == '':
        flash('Please select a valid Excel file', 'error')
        return redirect(url_for('payroll.manage_payroll'))

    try:
        if file.filename.endswith('.xlsx') or file.filename.endswith('.xls'):
            df = pd.read_excel(file)
        else:
            df = pd.read_csv(file)

        df.columns = [c.lower().strip() for c in df.columns]

        for _, row in df.iterrows():
            email = str(row.get('email', '')).strip()
            user = User.query.filter_by(email=email).first()
            
            if user:
                basic = float(row.get('basic_salary', 0))
                allow = float(row.get('allowances', 0))
                deduct = float(row.get('deductions', 0))
                net = basic + allow - deduct
                
                current_month = datetime.now().strftime("%B 2026")
                record = PayrollRecord.query.filter_by(user_id=user.id, month=current_month).first()
                
                if not record:
                    record = PayrollRecord(user_id=user.id, month=current_month)
                
                record.basic_salary = basic
                record.allowances = allow
                record.deductions = deduct
                record.net_salary = net
                record.status = "Processed"
                db.session.add(record)
        
        db.session.commit()
        flash('Excel Payroll imported successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Import Error: {str(e)}', 'error')

    return redirect(url_for('payroll.manage_payroll'))

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
    try:
        record = PayrollRecord.query.get_or_404(record_id)
        
        # KEY FIX: Pass variable as 'slip' to match your HTML template logic
        html = render_template("payslips/pdf_template.html", slip=record)

        # KEY FIX: Dynamic path for Linux Public Server
        if platform.system() == "Windows":
            path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
            config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
        else:
            path_wkhtmltopdf = '/usr/bin/wkhtmltopdf'
            config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

        options = {
            'page-size': 'A4',
            'encoding': "UTF-8",
            'no-outline': None,
            'quiet': ''
        }
        
        pdf = pdfkit.from_string(html, False, configuration=config, options=options)
        
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=Payslip_{record.user.email}_{record.month}.pdf'
        return response
    except Exception as e:
        current_app.logger.error(f"PDF Error: {str(e)}")
        flash("PDF service failed on server. Please ensure wkhtmltopdf is installed.", "danger")
        return redirect(url_for('payroll.manage_payroll'))