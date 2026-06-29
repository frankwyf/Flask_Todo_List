from flask import Blueprint, flash, jsonify, render_template, request

from app import bcrypt, db
from app.model import Task, Todoers


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def welcome():
    return render_template("login.html")


@auth_bp.route("/register")
def register():
    return render_template("register.html")


@auth_bp.route("/newlogin")
def newlogin():
    return render_template("login.html")


@auth_bp.route("/newAccount", methods=["POST", "GET"])
def newAccount():
    if request.method == "POST":
        newname = (request.form.get("name") or "").strip()
        email_value = (request.form.get("mailenter") or "").strip()
        psw = request.form.get("psw") or ""

        if not newname or not email_value or not psw:
            flash("All registration fields are required.", "error")
            return render_template("register.html")

        hashed_psw = bcrypt.generate_password_hash(psw).decode("utf-8")

        existing = Todoers.query.filter_by(username=newname).first()
        if existing:
            flash("That user name has been taken! pelase choose another one!", "error")
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

        flash("Your have registered successfully!", "success")
        return render_template("login.html", username=newname, password=psw)

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
            flash("No such user:" + testname + " ! Please register first!", "error")
            return render_template("login.html")

        if not bcrypt.check_password_hash(existing.password, testpassword):
            flash("Password is wrong! Please re-enter!", "error")
            return render_template("login.html")

        name = existing.username
        now = existing.id
        task_person = Task.query.filter_by(host=now).all()
        try:
            existing.status = 1
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return render_template("dolist.html", user=name, id=now, data=task_person)

    if request.method == "GET":
        return render_template("error.html", errormessage="Direct URL visit is not allowed!")

    return render_template("error.html")


@auth_bp.route("/clock.html")
def clock():
    return render_template("clock.html")


@auth_bp.route("/login.html")
def errorBack():
    return render_template("login.html")


@auth_bp.route("/logout/<int:id>")
def logout(id):
    user = Todoers.query.filter_by(id=id).first()
    if user:
        user.status = 0
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    return render_template("login.html")


@auth_bp.route("/portfolio/api")
def portfolio_api_docs():
    return render_template("portfolio_api.html")


@auth_bp.route("/portfolio/architecture")
def portfolio_architecture():
    return render_template("portfolio_architecture.html")


@auth_bp.route("/healthz")
def healthz():
    return jsonify({"status": "ok"})
