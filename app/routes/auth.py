import re

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app import bcrypt, db
from app.model import Todoers


auth_bp = Blueprint("auth", __name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@auth_bp.route("/")
def welcome():
    if current_user.is_authenticated:
        return redirect(url_for("task.backhome"))
    return render_template("login.html")


@auth_bp.route("/register")
def register():
    return render_template("register.html")


@auth_bp.route("/newlogin")
def newlogin():
    return redirect(url_for("auth.welcome"))


@auth_bp.route("/newAccount", methods=["POST", "GET"])
def newAccount():
    if request.method == "POST":
        newname = (request.form.get("name") or "").strip()
        email_value = (request.form.get("mailenter") or "").strip()
        psw = request.form.get("psw") or ""

        if not newname or not email_value or not psw:
            flash("All registration fields are required.", "error")
            return render_template("register.html")

        if not _EMAIL_RE.match(email_value):
            flash("Please enter a valid email address.", "error")
            return render_template("register.html")

        if len(psw) < 8:
            flash("Password must be at least 8 characters.", "error")
            return render_template("register.html")

        hashed_psw = bcrypt.generate_password_hash(psw).decode("utf-8")

        existing = Todoers.query.filter_by(username=newname).first()
        if existing:
            flash("That username has been taken! Please choose another one.", "error")
            return render_template("register.html")

        user = Todoers()
        user.username = newname
        user.password = hashed_psw
        user.Email = email_value
        user.status = 0
        try:
            db.session.add(user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        flash("Registration successful! Please log in.", "success")
        # Do NOT pre-fill password in the HTML response for security
        return render_template("login.html", username=newname)

    if request.method == "GET":
        return render_template("error.html", errormessage="Direct URL visit is not allowed!")

    return render_template("error.html")


@auth_bp.route("/doList", methods=["POST", "GET"])
def doList():
    if request.method == "POST":
        testname = (request.form.get("name") or "").strip()
        testpassword = request.form.get("psw") or ""
        existing = Todoers.query.filter_by(username=testname).first()

        if not existing:
            flash(f"No user '{testname}' found. Please register first.", "error")
            return render_template("login.html")

        if not bcrypt.check_password_hash(existing.password, testpassword):
            flash("Incorrect password. Please try again.", "error")
            return render_template("login.html")

        login_user(existing)

        try:
            existing.status = 1
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return redirect(url_for("task.backhome"))

    if request.method == "GET":
        return render_template("error.html", errormessage="Direct URL visit is not allowed!")

    return render_template("error.html")


@auth_bp.route("/logout")
@login_required
def logout():
    try:
        current_user.status = 0
        db.session.commit()
    except Exception:
        db.session.rollback()
    logout_user()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("auth.welcome"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_password = request.form.get("current_password") or ""
        new_password = request.form.get("new_password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        if not bcrypt.check_password_hash(current_user.password, current_password):
            flash("Current password is incorrect.", "error")
            return render_template("profile.html", user=current_user.username, id=current_user.id)

        if len(new_password) < 8:
            flash("New password must be at least 8 characters.", "error")
            return render_template("profile.html", user=current_user.username, id=current_user.id)

        if new_password != confirm_password:
            flash("New passwords do not match.", "error")
            return render_template("profile.html", user=current_user.username, id=current_user.id)

        try:
            current_user.password = bcrypt.generate_password_hash(new_password).decode("utf-8")
            db.session.commit()
            flash("Password updated successfully.", "success")
        except Exception:
            db.session.rollback()
            flash("An error occurred while updating password.", "error")

        return render_template("profile.html", user=current_user.username, id=current_user.id)

    return render_template("profile.html", user=current_user.username, id=current_user.id)


@auth_bp.route("/clock.html")
def clock():
    return render_template("clock.html")


@auth_bp.route("/login.html")
def errorBack():
    return redirect(url_for("auth.welcome"))


@auth_bp.route("/portfolio/api")
def portfolio_api_docs():
    return render_template("portfolio_api.html")


@auth_bp.route("/portfolio/architecture")
def portfolio_architecture():
    return render_template("portfolio_architecture.html")


@auth_bp.route("/healthz")
def healthz():
    return jsonify({"status": "ok"})
