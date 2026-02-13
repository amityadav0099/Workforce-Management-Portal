from flask import Blueprint, render_template, session, make_response
from payslips.models import Payslip
from accounts.decorators import login_required
import pdfkit

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
def download_payslip(slip_id):
    u_id = session.get("user_id")
    role = session.get("role")

    if role == "hr":
        slip = Payslip.query.get_or_404(slip_id)
    else:
        slip = Payslip.query.filter_by(id=slip_id, user_id=u_id).first_or_404()
    
    rendered = render_template("payslips/pdf_template.html", slip=slip)
    
    try:
        pdf = pdfkit.from_string(rendered, False)
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=Payslip_{slip.month}.pdf'
        return response
    except Exception as e:
        return f"PDF Error: {str(e)}", 500