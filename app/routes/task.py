import datetime
import csv
from collections import Counter
from io import StringIO

from flask import Blueprint, Response, current_app, flash, jsonify, render_template, request
from flask_mail import Message

from app import db, mail
from app.model import Task, Todoers


task_bp = Blueprint("task", __name__)


def _to_positive_int(raw_value, default):
    try:
        parsed = int(raw_value)
        if parsed <= 0:
            return default
        return parsed
    except (TypeError, ValueError):
        return default


def _to_int_or_none(raw_value):
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return None


def _serialize_task(task):
    return {
        "taskID": task.taskID,
        "module": task.module,
        "assessment": task.assessment,
        "create_date": str(task.create_date),
        "deadline": str(task.ddl),
        "remind": str(task.remind),
        "priority": task.priority,
        "status": task.status,
        "description": task.description,
        "host": task.host,
    }


def _parse_datetime(value):
    if not value:
        return None

    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _build_priority_distribution(tasks):
    priority_labels = {1: "Low", 2: "Medium", 3: "Significant", 4: "Urgent"}
    counter = Counter([priority_labels.get(task.priority, "Low") for task in tasks])
    ordered_labels = ["Low", "Medium", "Significant", "Urgent"]
    return {label: counter.get(label, 0) for label in ordered_labels}


def _build_module_distribution(tasks):
    module_counter = Counter([task.module for task in tasks if task.module])
    ordered = sorted(module_counter.items(), key=lambda item: (-item[1], item[0].lower()))
    return {name: count for name, count in ordered}


def _build_module_hotspots(tasks):
    module_counter = Counter([task.module for task in tasks if task.module])
    ordered = sorted(module_counter.items(), key=lambda item: (-item[1], item[0].lower()))
    return [{"name": name, "count": count} for name, count in ordered]


@task_bp.route("/sendReminders")
def sendReminders():
    user = request.args.get("user_name")
    uid = _to_int_or_none(request.args.get("user_id"))
    user_record = Todoers.query.filter_by(username=user).first()
    if not user_record or uid is None:
        flash("Unable to find the user email address.", "error")
        return render_template("error.html", errormessage="User account is not available.")

    today = datetime.date.today()
    send = Task.query.filter(Task.host == uid).all()
    for task_today in send:
        if not task_today.create_date or task_today.create_date.date() != today:
            continue
        msg = Message(
            subject="Todolist Reminder!",
            sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
            recipients=[user_record.Email],
        )
        msg.body = "This is a kindly remind of your Assement today: " + task_today.module + " : " + task_today.assessment
        mail.send(msg)

    flash("Check you E-mail box for remind messages! If none, then take your time!", "error")
    task_person = Task.query.filter_by(host=uid).all()
    return render_template("dolist.html", user=user, id=uid, data=task_person)


@task_bp.route("/backhome")
def backhome():
    user_name = request.args.get("user_name")
    user_id = _to_int_or_none(request.args.get("user_id"))
    if user_id is None:
        return render_template("error.html", errormessage="Invalid user id.")
    task_person = Task.query.filter_by(host=user_id).all()
    return render_template("dolist.html", user=user_name, id=user_id, data=task_person)


@task_bp.route("/createAss", methods=["POST", "GET"])
def createAss():
    if request.method == "POST":
        host = request.form.get("host")
        host_name = request.form.get("hostname")
        newModule = (request.form.get("moudleName") or "").strip()
        newAss = (request.form.get("ass") or "").strip()
        newcreate = datetime.datetime.now()
        newddl = _parse_datetime(request.form.get("deadline"))
        newremind = _parse_datetime(request.form.get("remind"))
        newdescription = "Word hard, play hard."
        newpri = _to_positive_int(request.form.get("priority"), 1)

        if not newModule or not newAss:
            flash("Module and assessment are required.", "error")
            task_person = Task.query.filter_by(host=host).all()
            return render_template("dolist.html", user=host_name, id=host, data=task_person)

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
        aim_ass.module = (request.form.get("editmoudle") or "").strip()
        aim_ass.assessment = (request.form.get("editass") or "").strip()
        aim_ass.create_date = _parse_datetime(dummy) or aim_ass.create_date
        aim_ass.ddl = _parse_datetime(request.form.get("deadline"))
        aim_ass.remind = _parse_datetime(request.form.get("reminder"))
        aim_ass.priority = _to_positive_int(request.form.get("priority"), aim_ass.priority or 1)
        aim_ass.status = _to_positive_int(request.form.get("status"), aim_ass.status or 0)
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
    uid = _to_int_or_none(request.args.get("user_id"))
    if uid is None:
        return render_template("error.html", errormessage="Invalid user id.")
    now_time = datetime.datetime.now()
    time_str = now_time.strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    return_data = Task.query.filter(Task.host == uid, Task.ddl < today).all()
    title = "Overdue Assessments"
    flash("These assessments are overdue!!! Pay more attetion next time", "error")
    return render_template("dolist.html", user=user, id=uid, tag=title, data=return_data)


@task_bp.route("/searchUpcoming")
def searchUpcoming():
    user = request.args.get("user_name")
    uid = _to_int_or_none(request.args.get("user_id"))
    if uid is None:
        return render_template("error.html", errormessage="Invalid user id.")
    days = min(_to_positive_int(request.args.get("days"), 7), 90)
    now = datetime.datetime.now()
    end = now + datetime.timedelta(days=days)
    return_data = Task.query.filter(Task.host == uid, Task.ddl >= now, Task.ddl <= end).all()
    title = f"Upcoming in {days} days"
    flash("Upcoming deadline list generated.", "error")
    return render_template("dolist.html", user=user, id=uid, tag=title, data=return_data)


@task_bp.route("/exportTasks")
def exportTasks():
    uid = _to_int_or_none(request.args.get("user_id"))
    if uid is None:
        return jsonify({"error": "user_id is required"}), 400
    user = request.args.get("user_name", "user")
    task_person = Task.query.filter_by(host=uid).all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["taskID", "module", "assessment", "deadline", "remind", "priority", "status", "description"])
    for task in task_person:
        writer.writerow([
            task.taskID,
            task.module,
            task.assessment,
            task.ddl,
            task.remind,
            task.priority,
            task.status,
            task.description,
        ])

    csv_content = output.getvalue()
    output.close()
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={user}_tasks.csv"},
    )


@task_bp.route("/api/tasks")
def tasks_api():
    uid = _to_int_or_none(request.args.get("user_id"))
    if uid is None:
        return jsonify({"error": "user_id is required"}), 400

    task_person = Task.query.filter_by(host=uid).all()
    payload = [_serialize_task(task) for task in task_person]
    return jsonify(payload)


@task_bp.route("/api/summary")
def tasks_summary_api():
    uid = _to_int_or_none(request.args.get("user_id"))
    if uid is None:
        return jsonify({"error": "user_id is required"}), 400

    task_person = Task.query.filter_by(host=uid).all()
    now = datetime.datetime.now()
    total = len(task_person)
    completed = len([task for task in task_person if task.status == 1])
    pending = len([task for task in task_person if task.status == 0])
    overdue = len([task for task in task_person if task.ddl and task.ddl < now and task.status == 0])
    upcoming_7_days = len(
        [
            task
            for task in task_person
            if task.ddl and now <= task.ddl <= (now + datetime.timedelta(days=7)) and task.status == 0
        ]
    )
    return jsonify({
        "total": total,
        "completed": completed,
        "pending": pending,
        "overdue": overdue,
        "upcoming_7_days": upcoming_7_days,
        "progress": int((completed * 100) / total) if total else 0,
    })


@task_bp.route("/api/insights")
def tasks_insights_api():
    uid = _to_int_or_none(request.args.get("user_id"))
    if uid is None:
        return jsonify({"error": "user_id is required"}), 400

    now = datetime.datetime.now()
    task_person = Task.query.filter_by(host=uid).all()
    total = len(task_person)
    completed = len([task for task in task_person if task.status == 1])
    pending_tasks = [task for task in task_person if task.status == 0]
    overdue = len([task for task in pending_tasks if task.ddl and task.ddl < now])
    urgent_open = len([task for task in pending_tasks if (task.priority or 0) >= 4])
    upcoming_7 = len(
        [task for task in pending_tasks if task.ddl and now <= task.ddl <= (now + datetime.timedelta(days=7))]
    )

    priority_distribution = _build_priority_distribution(task_person)
    module_distribution = _build_module_distribution(task_person)
    module_hotspots = _build_module_hotspots(task_person)

    completion_rate = round((completed / total) * 100, 2) if total else 0.0
    stability_rate = round(((len(pending_tasks) - overdue) / len(pending_tasks)) * 100, 2) if pending_tasks else 100.0
    productivity_score = round((completion_rate * 0.65) + (stability_rate * 0.35), 2)
    generated_at = (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

    return jsonify(
        {
            "generated_at": generated_at,
            "kpis": {
                "total": total,
                "completed": completed,
                "pending": len(pending_tasks),
                "overdue": overdue,
                "upcoming_7_days": upcoming_7,
                "urgent_open": urgent_open,
                "completion_rate": completion_rate,
                "stability_rate": stability_rate,
                "productivity_score": productivity_score,
            },
            "priority_distribution": priority_distribution,
            "module_distribution": module_distribution,
            "module_hotspots": module_hotspots,
        }
    )


@task_bp.route("/api/timeline")
def tasks_timeline_api():
    uid = _to_int_or_none(request.args.get("user_id"))
    if uid is None:
        return jsonify({"error": "user_id is required"}), 400

    days = min(_to_positive_int(request.args.get("days"), 14), 120)
    start_date = datetime.date.today()
    end_date = start_date + datetime.timedelta(days=days - 1)
    start_dt = datetime.datetime.combine(start_date, datetime.time.min)
    end_dt = datetime.datetime.combine(end_date + datetime.timedelta(days=1), datetime.time.min)

    timeline_tasks = Task.query.filter(
        Task.host == uid,
        Task.ddl.isnot(None),
        Task.ddl >= start_dt,
        Task.ddl < end_dt,
    ).order_by(Task.ddl.asc()).all()

    buckets = Counter(task.ddl.strftime("%Y-%m-%d") for task in timeline_tasks)
    dense_timeline = []
    for offset in range(days):
        date_key = (start_date + datetime.timedelta(days=offset)).strftime("%Y-%m-%d")
        dense_timeline.append({"date": date_key, "count": buckets.get(date_key, 0)})

    generated_at = (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

    return jsonify(
        {
            "generated_at": generated_at,
            "window_start": start_date.strftime("%Y-%m-%d"),
            "window_end": end_date.strftime("%Y-%m-%d"),
            "window_days": days,
            "total_deadlines": len(timeline_tasks),
            "timeline": dense_timeline,
        }
    )
