import os
import hashlib
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from functools import wraps
from flask import session, redirect, url_for, flash

load_dotenv()

#FERNET
FERNET_KEY = os.getenv("FERNET_KEY")
cipher = None

if not FERNET_KEY:
    print("[WARN] FERNET_KEY missing → encryption disabled")
else:
    try:
        cipher = Fernet(FERNET_KEY.encode())
        print(
            "[INFO] Fernet ready, key hash:",
            hashlib.sha256(FERNET_KEY.encode()).hexdigest()
        )
    except Exception as e:
        print("[ERROR] Invalid FERNET_KEY:", e)
        cipher = None

#AUTH DECORATORS
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Vui lòng đăng nhập trước", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get("role") != required_role:
                flash("Bạn không có quyền truy cập", "danger")
                return redirect(url_for("web_ui.dashboard"))
            return f(*args, **kwargs)
        return decorated
    return decorator
