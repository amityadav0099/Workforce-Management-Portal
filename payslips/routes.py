from flask import Blueprint, render_template, session, make_response
from flask import render_template, make_response, current_app, flash, redirect, url_for
from payslips.models import Payslip
from accounts.decorators import login_required
import pdfkit
import platform

payslips_bp = Blueprint("payslips", __name__, url_prefix="/payslips")

@payslips_bp.route("/")
@login_required
def view_payslips():
    role = session.get("role")
    u_id = session.get("user_id")

    if role == "hr":
        # HR sees all records
        data = Payslip.query.order_by(Payslip.id.desc()).all()
    else:
        # Filter by the logged-in user's ID
        data = Payslip.query.filter_by(user_id=u_id).order_by(Payslip.id.desc()).all()

    # Pass it as 'slips' to match your HTML template
    return render_template("payslips/my_view.html", slips=data)

@payslips_bp.route("/download/<int:slip_id>")
@login_required
def download_payslip(payslip_id):
    try:
        # 1. Fetch payslip data from your database
        payslip = Payslip.query.get_or_404(payslip_id)
        
        # 2. Render the HTML template specifically designed for PDF
        html = render_template('payslips/payslip_pdf_template.html', payslip=payslip)
        
        # 3. Handle Binary Path for Public Server (Render/Linux) vs Local (Windows)
        if platform.system() == "Windows":
            path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
            config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
        else:
            # On Render/Ubuntu, it is usually just 'wkhtmltopdf' in the PATH
            config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')

        # 4. PDF Options for better layout
        options = {
            'page-size': 'Letter',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'no-outline': None
        }

        # 5. Generate PDF
        pdf = pdfkit.from_string(html, False, configuration=config, options=options)
        
        # 6. Build the response
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=payslip_{payslip.id}.pdf'
        
        return response

    except Exception as e:
        print(f"PDF Error: {str(e)}")
        flash("PDF service is currently unavailable on this server. Please contact HR.", "danger")
        return redirect(url_for('payroll.manage_payroll'))