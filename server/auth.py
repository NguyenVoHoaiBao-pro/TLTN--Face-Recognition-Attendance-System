#auth.py
from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from .models import User
from .database import db

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password): 
            session["user_id"] = user.id
            session["username"] = user.username
            session["full_name"] = user.full_name
            session["role"] = user.role

            if user.role == "admin":
                return redirect(url_for("web_ui.admin_dashboard"))
            else:
                return redirect(url_for("web_ui.employee_dashboard"))
        
        flash("Sai tài khoản hoặc mật khẩu!", "danger")
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
