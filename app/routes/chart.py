import json

from flask import Blueprint, flash, render_template, request

from app.model import Task


chart_bp = Blueprint("chart", __name__)


@chart_bp.route("/visualPri")
def visualPri():
    user_name = request.args.get("name")
    user_id = request.args.get("uid")
    task_person = Task.query.filter_by(host=user_id).all()
    low = 0
    medium = 0
    sig = 0
    urgent = 0
    for test in task_person:
        if test.priority == 1:
            low = low + 1
        if test.priority == 2:
            medium = medium + 1
        if test.priority == 3:
            sig = sig + 1
        if test.priority == 4:
            urgent = urgent + 1
    pri = {"Low": low, "Medium": medium, "Significant": sig, "urgent": urgent}
    flash("Distribution of priority is generated.", "error")
    return render_template("dolist.html", user=user_name, id=user_id, draw_pie=1, data1=json.dumps(pri))


@chart_bp.route("/visualModule")
def visualModule():
    user_name = request.args.get("name")
    user_id = request.args.get("uid")
    task_person = Task.query.filter_by(host=user_id).all()
    module_list = []

    for test in task_person:
        module_list.append(test.module)
    unique_module_list = list(set(module_list))
    count = [0 for _ in range(0, len(unique_module_list))]
    for t in task_person:
        for i in unique_module_list:
            if t.module == i:
                count[unique_module_list.index(i)] = count[unique_module_list.index(i)] + 1

    module_distribution = dict(zip(unique_module_list, count))
    flash("Assessment distribution of each Module is generated.", "error")
    return render_template("dolist.html", user=user_name, id=user_id, draw_m=1, data2=json.dumps(module_distribution))


@chart_bp.route("/visualCompletion")
def visualCompletion():
    user_name = request.args.get("name")
    user_id = request.args.get("uid")
    task_person = Task.query.filter_by(host=user_id).all()
    counter = [0 for _ in range(0, 2)]

    for check in task_person:
        if check.status == 1:
            counter[0] = counter[0] + 1
        if check.status == 0:
            counter[1] = counter[1] + 1
    statuses = {"Completed": counter[0], "Undergoing": counter[1]}
    flash("Distribution of Completion is generated.", "error")
    return render_template("dolist.html", user=user_name, id=user_id, draw_d=1, data0=json.dumps(statuses))
