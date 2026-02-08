from functools import wraps
from flask import session, redirect, url_for, flash

# login required decorator
# def login_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if "username" not in session:
#             flash("Please login first", "warning")
#             return redirect(url_for("login"))
#         return f(*args, **kwargs)
#     return decorated_function
from functools import wraps
from flask import session, redirect, url_for

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper



# role based access decorator
def role_required(role):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "role" not in session:
                flash("Unauthorized access", "danger")
                return redirect(url_for("login"))

            if session.get("role") != role:
                flash("Access denied", "danger")
                return redirect(url_for("dashboard"))

            return f(*args, **kwargs)
        return decorated_function
    return wrapper
