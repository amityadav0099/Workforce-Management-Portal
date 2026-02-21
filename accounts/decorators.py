from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please login first", "warning")
            return redirect(url_for("accounts.login"))
        return f(*args, **kwargs)
    return wrapper

def role_required(role):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("accounts.login"))
            
            if current_user.role != role:
                flash("Access denied", "danger")
                return redirect(url_for("accounts.dashboard"))

            return f(*args, **kwargs)
        return decorated_function
    return wrapper