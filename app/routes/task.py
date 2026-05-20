import datetime

from flask import Blueprint, current_app, flash, render_template, request
from flask_mail import Message

from app import db, mail
from app.model import Task, Todoers


task_bp = Blueprint("task", __name__)


def _parse_datetime(value):
    if not value:
        return None

    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


@task_bp.route("/sendReminders")
def sendReminders():
    user = request.args.get("user_name")
    uid = request.args.get("user_id")
    send = Task.query.filter(
        Task.host == uid,
        db.cast(Task.create_date, db.DATE) == db.cast(datetime.datetime.utcnow(), db.DATE),
    ).all()
    for task_today in send:
        email_address = Todoers.query.filter_by(username=user).first().Email
        msg = Message(
            subject="Todolist Reminder!",
            sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
            recipients=[email_address],
        )
        msg.body = "This is a kindly remind of your Assement today: " + task_today.module + " : " + task_today.assessment
        mail.send(msg)

    flash("Check you E-mail box for remind messages! If none, then take your time!", "error")
    task_person = Task.query.filter_by(host=uid).all()
    return render_template("dolist.html", user=user, id=uid, data=task_person)


@task_bp.route("/backhome")
def backhome():
    user_name = request.args.get("user_name")
    user_id = request.args.get("user_id")
    task_person = Task.query.filter_by(host=user_id).all()
    return render_template("dolist.html", user=user_name, id=user_id, data=task_person)


@task_bp.route("/createAss", methods=["POST", "GET"])
def createAss():
    if request.method == "POST":
        host = request.form.get("host")
        host_name = request.form.get("hostname")
        newModule = request.form.get("moudleName")
        newAss = request.form.get("ass")
        newcreate = datetime.datetime.now()
        newddl = _parse_datetime(request.form.get("deadline"))
        newremind = _parse_datetime(request.form.get("remind"))
        newdescription = "Word hard, play hard."
        newpri = request.form.get("priority")

        task_person = Task.query.filter_by(host=host).all()
        for ass in task_person:
            if ass.module == newModule and ass.assessment == newAss:
                alert = newModule + " -- " + newAss + " already exixts!"
                flash(alert, "error")
                return render_template("dolist.html", user=host_name, id=host, data=task_person)

        aim = Task()
        aim.module = newModule
        aim.assessment = newAss
        aim.create_date = newcreate
        aim.ddl = newddl
        aim.remind = newremind
        aim.priority = newpri
        aim.description = newdescription
        aim.host = host
        try:
            db.session.add(aim)
            db.session.commit()
            tip = "New assessment: " + aim.module + "---" + aim.assessment + " has been added!"
        except Exception:
            db.session.rollback()
            tip = "Oops... something wrong with adding new assessment!"
            return render_template("error.html", errormessage=tip)

        task_person = Task.query.filter_by(host=host).all()
        flash(tip, "error")
        return render_template("dolist.html", user=host_name, id=host, data=task_person)

    if request.method == "GET":
        return render_template("error.html", errormessage="Direct URL visit is not allowed!")

    return render_template("error.html")


@task_bp.route("/completeTask")
def completeTask():
    target = request.args.get("aim")
    host_name = request.args.get("host")
    user_id = request.args.get("uid")
    task_aim = Task.query.filter_by(taskID=target).first()
    task_aim.status = 1
    try:
        db.session.commit()
        alert = "Assessemnet: " + task_aim.module + "--" + task_aim.assessment + " is completed!"
    except Exception:
        db.session.rollback()
        alert = "Oops... something wrong with completeing this assessment!"
        return render_template("error.html", errormessage=alert)

    task_person = Task.query.filter_by(host=user_id).all()
    flash(alert, "error")
    return render_template("dolist.html", user=host_name, id=user_id, data=task_person)


@task_bp.route("/undoTask")
def undoTask():
    target = request.args.get("aim")
    host_name = request.args.get("host")
    user_id = request.args.get("uid")
    task_aim = Task.query.filter_by(taskID=target).first()
    task_aim.status = 0
    try:
        db.session.commit()
        alert = "Assessemnet: " + task_aim.module + "--" + task_aim.assessment + " completion is undone!"
    except Exception:
        db.session.rollback()
        alert = "Oops... something wrong with undoing this assessment's completion!"
        return render_template("error.html", errormessage=alert)

    task_person = Task.query.filter_by(host=user_id).all()
    flash(alert, "error")
    return render_template("dolist.html", user=host_name, id=user_id, data=task_person)


@task_bp.route("/deleteTask")
def deleteTask():
    target = request.args.get("aim")
    host_name = request.args.get("host")
    user_id = request.args.get("uid")
    task_aim = Task.query.filter_by(taskID=target).first()
    try:
        db.session.delete(task_aim)
        db.session.commit()
        alert = "Assessemnet: " + task_aim.module + "--" + task_aim.assessment + " is deleted!"
    except Exception:
        db.session.rollback()
        alert = "Oops... something wrong with deleteing the assessment!"
        return render_template("error.html", errormessage=alert)

    task_person = Task.query.filter_by(host=user_id).all()
    flash(alert, "error")
    return render_template("dolist.html", user=host_name, id=user_id, data=task_person)


@task_bp.route("/edit")
def edit():
    target = request.args.get("edit")
    host_name = request.args.get("host_return")
    user_id = request.args.get("uid_return")
    task_aim = Task.query.filter_by(taskID=target).all()
    deadline = datetime.datetime.strftime(task_aim[0].ddl, "%Y-%m-%dT%H:%M")
    remindtime = datetime.datetime.strftime(task_aim[0].remind, "%Y-%m-%dT%H:%M")
    return render_template(
        "edit.html",
        user=host_name,
        id=user_id,
        data=task_aim,
        target_ddl=deadline,
        target_remind=remindtime,
    )


@task_bp.route("/subEdit", methods=["POST", "GET"])
def subEdit():
    if request.method == "POST":
        edit_aim = request.form.get("this_task")
        user_id = request.form.get("host")
        host_name = request.form.get("uid")
        dummy = request.form.get("create")

        aim_ass = Task.query.filter_by(taskID=edit_aim).first()
        aim_ass.taskID = edit_aim
        aim_ass.module = request.form.get("editmoudle")
        aim_ass.assessment = request.form.get("editass")
        aim_ass.create_date = _parse_datetime(dummy) or aim_ass.create_date
        aim_ass.ddl = _parse_datetime(request.form.get("deadline"))
        aim_ass.remind = _parse_datetime(request.form.get("reminder"))
        aim_ass.priority = request.form.get("priority")
        aim_ass.status = request.form.get("status")
        aim_ass.host = user_id
        aim_ass.description = request.form.get("descri")

        try:
            db.session.add(aim_ass)
            db.session.commit()
            mess = request.form.get("editmoudle") + " -- " + request.form.get("editass") + " has been updated!"
        except Exception:
            db.session.rollback()
            mess = "Oops... Edit not successful with some database error"
            return render_template("error.html", errormessage=mess)

        flash(mess, "error")
        task_person = Task.query.filter_by(host=user_id).all()
        return render_template("dolist.html", user=host_name, id=user_id, data=task_person)

    if request.method == "GET":
        return render_template("error.html", errormessage="Direct URL visit is not allowed!")

    return render_template("error.html")


@task_bp.route("/discard")
def discard():
    host_name = request.args.get("host")
    user_id = request.args.get("uid")
    task_person = Task.query.filter_by(host=user_id).all()
    return render_template("dolist.html", user=host_name, id=user_id, data=task_person)


@task_bp.route("/searchStatus", methods=["POST", "GET"])
def searchStatus():
    if request.method == "POST":
        user_id = request.form.get("host")
        host_name = request.form.get("uid")
        state = request.form.get("completion")
        title = ""
        if state == "1":
            title = "Completed Assessments"
        elif state == "0":
            title = "Undergoing tasks"

        return_tasks = Task.query.filter_by(host=user_id, status=state).all()
        flash(title + " is shown", "error")
        return render_template("dolist.html", user=host_name, id=user_id, data=return_tasks, tag=title)

    if request.method == "GET":
        return render_template("error.html", errormessage="Direct URL visit is not allowed!")

    return render_template("error.html")


@task_bp.route("/searchmName", methods=["POST", "GET"])
def searchmName():
    if request.method == "POST":
        user_id = request.form.get("host")
        host_name = request.form.get("uid")
        moduleTitle = request.form.get("listName")

        return_tasks = Task.query.filter_by(host=user_id, module=moduleTitle).all()
        flash(moduleTitle + "'s assessments is shown", "error")
        return render_template("dolist.html", user=host_name, id=user_id, data=return_tasks, tag=moduleTitle)

    if request.method == "GET":
        return render_template("error.html", errormessage="Direct URL visit is not allowed!")

    return render_template("error.html")


@task_bp.route("/searchaName", methods=["POST", "GET"])
def searchaName():
    if request.method == "POST":
        user_id = request.form.get("host")
        host_name = request.form.get("uid")
        assTitle = request.form.get("listName")

        return_tasks = Task.query.filter_by(host=user_id, assessment=assTitle).all()
        title = '"' + assTitle + '" in all Module'
        flash('"' + assTitle + '" in all module is shown', "error")
        return render_template("dolist.html", user=host_name, id=user_id, data=return_tasks, tag=title)

    if request.method == "GET":
        return render_template("error.html", errormessage="Direct URL visit is not allowed!")

    return render_template("error.html")


@task_bp.route("/searchOverdue")
def searchOverdue():
    user = request.args.get("user_name")
    uid = request.args.get("user_id")
    now_time = datetime.datetime.now()
    time_str = now_time.strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    return_data = Task.query.filter(Task.ddl < today).all()
    title = "Overdue Assessments"
    flash("These assessments are overdue!!! Pay more attetion next time", "error")
    return render_template("dolist.html", user=user, id=uid, tag=title, data=return_data)
