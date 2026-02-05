from flask import Blueprint, render_template, session, redirect, url_for
from .models import Payslip
from models import db



payslips_bp = Blueprint("payslips", __name__, url_prefix="/payslips")

@payslips_bp.route("/payslips")
def view_payslips():
    if session.get("role") != "hr":
        return redirect(url_for("dashboard"))

    payslips = Payslip.query.all()
    return render_template("payslips/payslips.html", payslips=payslips)

