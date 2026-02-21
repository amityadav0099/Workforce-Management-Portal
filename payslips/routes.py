from flask import Blueprint, render_template, session, make_response, current_app, flash, redirect, url_for
from accounts.decorators import login_required
import pdfkit
import platform
import os
from payroll.models import PayrollRecord

payslips_bp = Blueprint("payslips", __name__, url_prefix="/payslips")

@payslips_bp.route("/")
@login_required
def view_payslips():
    u_id = session.get("user_id")
    role = session.get("role")

    if role == "hr":
        # HR sees everything processed in the 'payroll' table
        data = PayrollRecord.query.order_by(PayrollRecord.id.desc()).all()
    else:
        # Employees see only their records based on user_id
        data = PayrollRecord.query.filter_by(user_id=u_id).order_by(PayrollRecord.id.desc()).all()

    return render_template("payslips/my_view.html", slips=data)

@payslips_bp.route("/download/<int:slip_id>")
@login_required
def download_payslip(slip_id):
    try:
        # 1. Fetch payslip data - named 'slip' to match your template
        slip = PayrollRecord.query.get_or_404(slip_id)
        
        # 2. Render HTML template
        html = render_template('payslips/pdf_template.html', slip=slip)
        
        # 3. Handle Binary Path
        if platform.system() == "Windows":
            path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
        else:
            # Standard path for Linux/Render
            path_wkhtmltopdf = '/usr/bin/wkhtmltopdf'

        # Safety check: if binary doesn't exist, try local path
        if not os.path.exists(path_wkhtmltopdf) and platform.system() != "Windows":
            path_wkhtmltopdf = '/usr/local/bin/wkhtmltopdf'

        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

        # 4. PDF Options
        options = {
            'page-size': 'Letter',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'no-outline': None,
            'enable-local-file-access': None
        }

        # 5. Generate PDF binary
        pdf = pdfkit.from_string(html, False, configuration=config, options=options)
        
        # 6. Build the response
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=payslip_{slip_id}.pdf'
        
        return response

    except Exception as e:
        # Log exact error to Render console
        print(f"CRITICAL PDF ERROR: {str(e)}")
        flash(f"PDF Service Error: {str(e)}", "rose")
        return redirect(url_for('payslips.view_payslips'))