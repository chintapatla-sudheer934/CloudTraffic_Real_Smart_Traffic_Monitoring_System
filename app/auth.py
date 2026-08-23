from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from werkzeug.security import check_password_hash
from .models import User, AuditLog
from . import db

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            db.session.add(AuditLog(action="LOGIN", details=f"Login: {email}", user_id=user.id))
            db.session.commit()
            return redirect(url_for("main.dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    if current_user.is_authenticated:
        db.session.add(AuditLog(action="LOGOUT", details=f"Logout: {current_user.email}", user_id=current_user.id))
        db.session.commit()
    logout_user()
    return redirect(url_for("auth.login"))
