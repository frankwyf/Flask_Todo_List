import json

from flask import Blueprint, flash, render_template
from flask_login import current_user, login_required

from app.model import Task


chart_bp = Blueprint("chart", __name__)


@chart_bp.route("/visualPri")
@login_required
def visualPri():
    uid = current_user.id
    task_person = Task.query.filter_by(host=uid).all()
    low = medium = sig = urgent = 0
    for test in task_person:
        if test.priority == 1:
            low += 1
        elif test.priority == 2:
            medium += 1
        elif test.priority == 3:
            sig += 1
        elif test.priority == 4:
            urgent += 1
    pri = {"Low": low, "Medium": medium, "Significant": sig, "Urgent": urgent}
    flash("Priority distribution chart generated.", "info")
    return render_template("dolist.html", user=current_user.username, id=uid, draw_pie=1, data1=json.dumps(pri))


@chart_bp.route("/visualModule")
@login_required
def visualModule():
    uid = current_user.id
    task_person = Task.query.filter_by(host=uid).all()
    unique_module_list = list({task.module for task in task_person if task.module})
    module_distribution = {m: sum(1 for t in task_person if t.module == m) for m in unique_module_list}
    flash("Module distribution chart generated.", "info")
    return render_template("dolist.html", user=current_user.username, id=uid, draw_m=1, data2=json.dumps(module_distribution))


@chart_bp.route("/visualCompletion")
@login_required
def visualCompletion():
    uid = current_user.id
    task_person = Task.query.filter_by(host=uid).all()
    completed = sum(1 for t in task_person if t.status == 1)
    undergoing = sum(1 for t in task_person if t.status == 0)
    statuses = {"Completed": completed, "Pending": undergoing}
    flash("Completion distribution chart generated.", "info")
    return render_template("dolist.html", user=current_user.username, id=uid, draw_d=1, data0=json.dumps(statuses))
