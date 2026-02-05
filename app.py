from flask import Flask, render_template, request, redirect, url_for, session
from accounts.decorators import login_required, role_required
from models import Grievance, Notification   
from payslips.routes import payslips_bp
from leaves.routes import leaves_bp
from payslips.routes import payslips_bp
from accounts.routes import accounts_bp
from extensions import db
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = "supersecretkey"


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "hr_portal.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)   

app.register_blueprint(leaves_bp)
app.register_blueprint(payslips_bp)
app.register_blueprint(accounts_bp, url_prefix= "/accounts")


# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "hr" and password == "123":
            session["role"] = "hr"
            session["username"] = "hr"
            return redirect(url_for("dashboard"))

        if username == "employee" and password == "123":
            session["role"] = "employee"
            session["username"] = "employee"
            return redirect(url_for("dashboard"))

        return "Invalid credentials"

    return render_template("login.html")

# ================= DASHBOARD =================
@login_required
@app.route("/dashboard")
def dashboard():
    if "role" not in session:
        return redirect(url_for("login"))

    total = Grievance.query.count()
    pending = Grievance.query.filter_by(status="Open").count()
    resolved = Grievance.query.filter_by(status="Resolved").count()

    # last 5 grievances (role wise)
    if session["role"] == "employee":
        recent_grievances = Grievance.query.filter_by(
            created_by=session["username"]
        ).order_by(Grievance.id.desc()).limit(5).all()
    else:
        recent_grievances = Grievance.query.order_by(
            Grievance.id.desc()
        ).limit(5).all()

    # 🔔 NOTIFICATION: employee ke liye notifications
    notifications = Notification.query.filter_by(
        user=session["username"]
    ).order_by(Notification.id.desc()).limit(5).all()

    return render_template(
        "dashboard.html",
        role=session["role"],
        total=total,
        pending=pending,
        resolved=resolved,
        recent_grievances=recent_grievances,
        notifications=notifications   # 🔔 NOTIFICATION send to dashboard
    )


# ================= ADD GRIEVANCE (EMPLOYEE) =================
@app.route("/add-grievance", methods=["GET", "POST"])
def add_grievance():
    if session.get("role") != "employee":
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]

        g = Grievance(
            title=title,
            description=description,
            created_by=session["username"]
        )

        db.session.add(g)
        db.session.commit()

        return redirect(url_for("dashboard"))

    return render_template("add_grievance.html")


# ================= VIEW GRIEVANCES =================
@app.route("/grievances")
@login_required
@role_required("hr")
def grievances_page():
    if "role" not in session:
        return redirect(url_for("login"))

    status = request.args.get("status")

    query = Grievance.query

    if session["role"] == "employee":
        query = query.filter_by(created_by=session["username"])

    if status:
        query = query.filter_by(status=status)

    grievances = query.all()

    return render_template(
        "grievances.html",
        grievances=grievances,
        role=session["role"]
    )


# ================= RESOLVE (HR ONLY) =================
@app.route("/resolve/<int:id>")
@login_required
@role_required("hr")
def resolve_grievance(id):
    grievance = Grievance.query.get_or_404(id)
    grievance.status = "Resolved"

    # 🔔 NOTIFICATION: employee ko bhejo
    notification = Notification(
        user=grievance.created_by,
        message="Your grievance has been resolved by HR"
    )
    db.session.add(notification)

    db.session.commit()
    return redirect(url_for("grievances_page"))


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ================= RUN =================
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)














