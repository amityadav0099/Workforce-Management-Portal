from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from extensions import db
from .models import EmployeeProfile

accounts_bp = Blueprint("accounts", __name__, url_prefix="/accounts")


@accounts_bp.route("/my-profile", methods=["GET", "POST"])
def my_profile():

    username = session.get("username")

    if not username:
        flash("Please login first", "danger")
        return redirect(url_for("login"))  # adjust if needed

    profile = EmployeeProfile.query.filter_by(username=username).first()

    if request.method == "POST":

        if not profile:
            profile = EmployeeProfile(username=username)

        # BASIC DETAILS
        profile.name = request.form.get("name")
        profile.mobile = request.form.get("mobile")
        profile.email = request.form.get("email")
        profile.address = request.form.get("address")

        # DATE FIELDS
        dob = request.form.get("dob")
        joining_date = request.form.get("joining_date")

        profile.dob = (
            datetime.strptime(dob, "%Y-%m-%d").date()
            if dob else None
        )

        profile.joining_date = (
            datetime.strptime(joining_date, "%Y-%m-%d").date()
            if joining_date else None
        )

        db.session.add(profile)
        db.session.commit()

        flash("Profile updated successfully", "success")
        return redirect(url_for("accounts.my_profile"))

    return render_template("accounts/my_profile.html", profile=profile)