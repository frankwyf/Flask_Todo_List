import datetime
import csv
from collections import Counter
from io import StringIO

from flask import Blueprint, Response, abort, current_app, flash, jsonify, render_template, request
from flask_login import current_user, login_required
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


def _api_error(message, status_code=400, code="bad_request"):
    return jsonify({"error": message, "error_detail": {"code": code, "message": message}}), status_code


@task_bp.route("/sendReminders")
@login_required
def sendReminders():
    uid = current_user.id
    user = current_user.username
    user_record = Todoers.query.get(uid)

    today = datetime.date.today()
    send = Task.query.filter(Task.host == uid).all()
    for task_today in send:
        if not task_today.create_date or task_today.create_date.date() != today:
            continue
        msg = Message(
            subject="Todo-List Reminder!",
            sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
            recipients=[user_record.Email],
        )
        msg.body = f"Reminder for your assessment today: {task_today.module} : {task_today.assessment}"
        mail.send(msg)

    flash("Check your email for reminder messages!", "success")
    task_person = Task.query.filter_by(host=uid).all()
    return render_template("dolist.html", user=user, id=uid, data=task_person)


@task_bp.route("/backhome")
@login_required
def backhome():
    uid = current_user.id
    task_person = Task.query.filter_by(host=uid).all()
    return render_template("dolist.html", user=current_user.username, id=uid, data=task_person)


@task_bp.route("/createAss", methods=["POST", "GET"])
@login_required
def createAss():
    if request.method == "POST":
        uid = current_user.id
        username = current_user.username
        newModule = (request.form.get("moudleName") or "").strip()
        newAss = (request.form.get("ass") or "").strip()
        newcreate = datetime.datetime.now()
        newddl = _parse_datetime(request.form.get("deadline"))
        newremind = _parse_datetime(request.form.get("remind"))
        newdescription = (request.form.get("description") or "").strip()
        newpri = _to_positive_int(request.form.get("priority"), 1)

        if not newModule or not newAss:
            flash("Module and assessment name are required.", "error")
            task_person = Task.query.filter_by(host=uid).all()
            return render_template("dolist.html", user=username, id=uid, data=task_person)

        task_person = Task.query.filter_by(host=uid).all()
        for ass in task_person:
            if ass.module == newModule and ass.assessment == newAss:
                flash(f"{newModule} -- {newAss} already exists!", "error")
                return render_template("dolist.html", user=username, id=uid, data=task_person)

        aim = Task()
        aim.module = newModule
        aim.assessment = newAss
        aim.create_date = newcreate
        aim.ddl = newddl
        aim.remind = newremind
        aim.priority = newpri
        aim.description = newdescription
        aim.host = uid
        try:
            db.session.add(aim)
            db.session.commit()
            flash(f"New assessment: {aim.module} — {aim.assessment} has been added!", "success")
        except Exception:
            db.session.rollback()
            return render_template("error.html", errormessage="Failed to add assessment. Please try again.")

        task_person = Task.query.filter_by(host=uid).all()
        return render_template("dolist.html", user=username, id=uid, data=task_person)

    if request.method == "GET":
        return render_template("error.html", errormessage="Direct URL visit is not allowed!")

    return render_template("error.html")


@task_bp.route("/completeTask")
@login_required
def completeTask():
    target = request.args.get("aim")
    uid = current_user.id
    task_aim = Task.query.filter_by(taskID=target, host=uid).first()
    if task_aim is None:
        abort(403)
    task_aim.status = 1
    try:
        db.session.commit()
        flash(f"Assessment: {task_aim.module} — {task_aim.assessment} is completed!", "success")
    except Exception:
        db.session.rollback()
        return render_template("error.html", errormessage="Failed to complete assessment.")

    task_person = Task.query.filter_by(host=uid).all()
    return render_template("dolist.html", user=current_user.username, id=uid, data=task_person)


@task_bp.route("/undoTask")
@login_required
def undoTask():
    target = request.args.get("aim")
    uid = current_user.id
    task_aim = Task.query.filter_by(taskID=target, host=uid).first()
    if task_aim is None:
        abort(403)
    task_aim.status = 0
    try:
        db.session.commit()
        flash(f"Assessment: {task_aim.module} — {task_aim.assessment} completion undone.", "info")
    except Exception:
        db.session.rollback()
        return render_template("error.html", errormessage="Failed to undo completion.")

    task_person = Task.query.filter_by(host=uid).all()
    return render_template("dolist.html", user=current_user.username, id=uid, data=task_person)


@task_bp.route("/deleteTask")
@login_required
def deleteTask():
    target = request.args.get("aim")
    uid = current_user.id
    task_aim = Task.query.filter_by(taskID=target, host=uid).first()
    if task_aim is None:
        abort(403)
    module, assessment = task_aim.module, task_aim.assessment
    try:
        db.session.delete(task_aim)
        db.session.commit()
        flash(f"Assessment: {module} — {assessment} has been removed.", "success")
    except Exception:
        db.session.rollback()
        return render_template("error.html", errormessage="Failed to delete assessment.")

    task_person = Task.query.filter_by(host=uid).all()
    return render_template("dolist.html", user=current_user.username, id=uid, data=task_person)


@task_bp.route("/edit")
@login_required
def edit():
    target = request.args.get("edit")
    uid = current_user.id
    task_aim = Task.query.filter_by(taskID=target, host=uid).all()
    if not task_aim:
        abort(403)
    deadline = datetime.datetime.strftime(task_aim[0].ddl, "%Y-%m-%dT%H:%M") if task_aim[0].ddl else ""
    remindtime = datetime.datetime.strftime(task_aim[0].remind, "%Y-%m-%dT%H:%M") if task_aim[0].remind else ""
    return render_template(
        "edit.html",
        user=current_user.username,
        id=uid,
        data=task_aim,
        target_ddl=deadline,
        target_remind=remindtime,
    )


@task_bp.route("/subEdit", methods=["POST", "GET"])
@login_required
def subEdit():
    if request.method == "POST":
        edit_aim = request.form.get("this_task")
        uid = current_user.id

        aim_ass = Task.query.filter_by(taskID=edit_aim, host=uid).first()
        if aim_ass is None:
            abort(403)

        aim_ass.module = (request.form.get("editmoudle") or "").strip()
        aim_ass.assessment = (request.form.get("editass") or "").strip()
        create_raw = request.form.get("create")
        aim_ass.create_date = _parse_datetime(create_raw) or aim_ass.create_date
        aim_ass.ddl = _parse_datetime(request.form.get("deadline"))
        aim_ass.remind = _parse_datetime(request.form.get("reminder"))
        aim_ass.priority = _to_positive_int(request.form.get("priority"), aim_ass.priority or 1)
        aim_ass.status = _to_positive_int(request.form.get("status"), aim_ass.status or 0)
        aim_ass.description = (request.form.get("descri") or "").strip()

        try:
            db.session.add(aim_ass)
            db.session.commit()
            flash(f"{aim_ass.module} — {aim_ass.assessment} has been updated!", "success")
        except Exception:
            db.session.rollback()
            return render_template("error.html", errormessage="Update failed. Please try again.")

        task_person = Task.query.filter_by(host=uid).all()
        return render_template("dolist.html", user=current_user.username, id=uid, data=task_person)

    if request.method == "GET":
        return render_template("error.html", errormessage="Direct URL visit is not allowed!")

    return render_template("error.html")


@task_bp.route("/discard")
@login_required
def discard():
    uid = current_user.id
    task_person = Task.query.filter_by(host=uid).all()
    return render_template("dolist.html", user=current_user.username, id=uid, data=task_person)


@task_bp.route("/searchStatus", methods=["POST", "GET"])
@login_required
def searchStatus():
    if request.method == "POST":
        uid = current_user.id
        state = request.form.get("completion")
        title = "Completed Assessments" if state == "1" else "Pending Assessments"
        return_tasks = Task.query.filter_by(host=uid, status=state).all()
        flash(f"{title} shown.", "info")
        return render_template("dolist.html", user=current_user.username, id=uid, data=return_tasks, tag=title)

    if request.method == "GET":
        return render_template("error.html", errormessage="Direct URL visit is not allowed!")

    return render_template("error.html")


@task_bp.route("/searchmName", methods=["POST", "GET"])
@login_required
def searchmName():
    if request.method == "POST":
        uid = current_user.id
        moduleTitle = (request.form.get("listName") or "").strip()
        return_tasks = Task.query.filter_by(host=uid, module=moduleTitle).all()
        flash(f"Module '{moduleTitle}' assessments shown.", "info")
        return render_template("dolist.html", user=current_user.username, id=uid, data=return_tasks, tag=moduleTitle)

    if request.method == "GET":
        return render_template("error.html", errormessage="Direct URL visit is not allowed!")

    return render_template("error.html")


@task_bp.route("/searchaName", methods=["POST", "GET"])
@login_required
def searchaName():
    if request.method == "POST":
        uid = current_user.id
        assTitle = (request.form.get("listName") or "").strip()
        return_tasks = Task.query.filter_by(host=uid, assessment=assTitle).all()
        title = f'"{assTitle}" across all modules'
        flash(f'Assessment "{assTitle}" search results shown.', "info")
        return render_template("dolist.html", user=current_user.username, id=uid, data=return_tasks, tag=title)

    if request.method == "GET":
        return render_template("error.html", errormessage="Direct URL visit is not allowed!")

    return render_template("error.html")


@task_bp.route("/searchOverdue")
@login_required
def searchOverdue():
    uid = current_user.id
    now_time = datetime.datetime.now()
    return_data = Task.query.filter(Task.host == uid, Task.ddl < now_time, Task.status == 0).all()
    title = "Overdue Assessments"
    flash("Overdue assessments are shown. Plan ahead!", "warning")
    return render_template("dolist.html", user=current_user.username, id=uid, tag=title, data=return_data)


@task_bp.route("/searchUpcoming")
@login_required
def searchUpcoming():
    uid = current_user.id
    days = min(_to_positive_int(request.args.get("days"), 7), 90)
    now = datetime.datetime.now()
    end = now + datetime.timedelta(days=days)
    return_data = Task.query.filter(Task.host == uid, Task.ddl >= now, Task.ddl <= end, Task.status == 0).all()
    title = f"Upcoming in {days} days"
    flash(f"Upcoming deadline list for next {days} days.", "info")
    return render_template("dolist.html", user=current_user.username, id=uid, tag=title, data=return_data)


@task_bp.route("/exportTasks")
@login_required
def exportTasks():
    uid = current_user.id
    user = current_user.username
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
@login_required
def tasks_api():
    uid = current_user.id
    task_person = Task.query.filter_by(host=uid).all()
    payload = [_serialize_task(task) for task in task_person]
    generated_at = (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    return jsonify({
        "generated_at": generated_at,
        "total": len(payload),
        "items": payload,
    })


@task_bp.route("/api/summary")
@login_required
def tasks_summary_api():
    uid = current_user.id
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
    progress_rate = round((completed * 100.0) / total, 2) if total else 0.0
    generated_at = (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    return jsonify({
        "generated_at": generated_at,
        "total": total,
        "completed": completed,
        "pending": pending,
        "overdue": overdue,
        "upcoming_7_days": upcoming_7_days,
        "progress_rate": progress_rate,
        "progress": int((completed * 100) / total) if total else 0,
    })


@task_bp.route("/api/insights")
@login_required
def tasks_insights_api():
    uid = current_user.id

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
@login_required
def tasks_timeline_api():
    uid = current_user.id

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


@task_bp.route("/api/batch", methods=["POST"])
@login_required
def tasks_batch_api():
    uid = current_user.id
    payload = request.get_json(silent=True) or {}
    action = payload.get("action")
    task_ids = payload.get("task_ids", [])

    if action not in ("complete", "delete", "undo"):
        return _api_error("Invalid action. Use 'complete', 'delete', or 'undo'.", code="invalid_action")

    if not task_ids or not isinstance(task_ids, list):
        return _api_error("task_ids must be a non-empty list.", code="missing_ids")

    # Limit batch size to prevent abuse
    task_ids = [int(tid) for tid in task_ids[:50] if str(tid).isdigit()]

    tasks = Task.query.filter(Task.taskID.in_(task_ids), Task.host == uid).all()
    affected = 0

    try:
        for task in tasks:
            if action == "complete":
                task.status = 1
            elif action == "undo":
                task.status = 0
            elif action == "delete":
                db.session.delete(task)
            affected += 1
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _api_error("Batch operation failed.", 500, code="batch_error")

    return jsonify({"action": action, "affected": affected})
