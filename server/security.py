
from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapper

def role_required(role):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if session.get("role") != role:
                flash("Bạn không có quyền truy cập!")
                return redirect(url_for("auth.login"))
            return view(*args, **kwargs)
        return wrapper
    return decorator
