import datetime as dt

from app import db, mail
from app.model import Task, Todoers


def _create_user(client, username="bob", email="bob@example.com"):
    with client.application.app_context():
        user = Todoers(username=username, password="hashed", Email=email, status=0)
        db.session.add(user)
        db.session.commit()
        return user.id


def _create_task(client, user_id, module="Math", assessment="Quiz", status=0, days=2):
    now = dt.datetime.now()
    with client.application.app_context():
        task = Task(
            module=module,
            assessment=assessment,
            create_date=now,
            ddl=now + dt.timedelta(days=days),
            remind=now + dt.timedelta(days=1),
            description="desc",
            priority=2,
            status=status,
            host=user_id,
        )
        db.session.add(task)
        db.session.commit()
        return task.taskID


def test_auth_duplicate_username_and_direct_get_guard(client):
    response = client.get("/newAccount")
    assert response.status_code == 200
    assert b"Direct URL visit is not allowed" in response.data

    first = client.post(
        "/newAccount",
        data={"name": "dup", "mailenter": "dup1@example.com", "psw": "Password123"},
    )
    assert first.status_code == 200

    second = client.post(
        "/newAccount",
        data={"name": "dup", "mailenter": "dup2@example.com", "psw": "Password123"},
    )
    assert second.status_code == 200
    assert b"has been taken" in second.data


def test_task_post_only_endpoints_reject_get(client):
    for path in ["/createAss", "/subEdit", "/searchStatus", "/searchmName", "/searchaName"]:
        response = client.get(path)
        assert response.status_code == 200
        assert b"Direct URL visit is not allowed" in response.data


def test_duplicate_assessment_create_is_blocked(client):
    user_id = _create_user(client, username="alice")
    _create_task(client, user_id=user_id, module="Web", assessment="Final")

    response = client.post(
        "/createAss",
        data={
            "host": str(user_id),
            "hostname": "alice",
            "moudleName": "Web",
            "ass": "Final",
            "deadline": (dt.datetime.now() + dt.timedelta(days=4)).strftime("%Y-%m-%dT%H:%M"),
            "remind": (dt.datetime.now() + dt.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M"),
            "priority": "2",
        },
    )

    assert response.status_code == 200
    assert b"already exixts" in response.data


def test_search_export_and_api_summary(client):
    user_id = _create_user(client, username="sam")
    _create_task(client, user_id=user_id, module="DB", assessment="Lab", status=1, days=3)
    _create_task(client, user_id=user_id, module="AI", assessment="Project", status=0, days=-1)

    status_response = client.post(
        "/searchStatus",
        data={"host": str(user_id), "uid": "sam", "completion": "1"},
    )
    assert status_response.status_code == 200
    assert b"Completed Assessments" in status_response.data

    module_response = client.post(
        "/searchmName",
        data={"host": str(user_id), "uid": "sam", "listName": "DB"},
    )
    assert module_response.status_code == 200
    assert b"DB" in module_response.data

    ass_response = client.post(
        "/searchaName",
        data={"host": str(user_id), "uid": "sam", "listName": "Project"},
    )
    assert ass_response.status_code == 200
    assert b"Project" in ass_response.data

    overdue_response = client.get(f"/searchOverdue?user_id={user_id}&user_name=sam")
    assert overdue_response.status_code == 200
    assert b"Overdue Assessments" in overdue_response.data

    upcoming_response = client.get(f"/searchUpcoming?user_id={user_id}&user_name=sam&days=7")
    assert upcoming_response.status_code == 200
    assert b"Upcoming in 7 days" in upcoming_response.data

    export_response = client.get(f"/exportTasks?user_id={user_id}&user_name=sam")
    assert export_response.status_code == 200
    assert export_response.mimetype == "text/csv"
    assert b"taskID,module,assessment,deadline,remind,priority,status,description" in export_response.data

    tasks_api = client.get(f"/api/tasks?user_id={user_id}")
    assert tasks_api.status_code == 200
    payload = tasks_api.get_json()
    assert len(payload) == 2

    summary_api = client.get(f"/api/summary?user_id={user_id}")
    assert summary_api.status_code == 200
    summary = summary_api.get_json()
    assert summary == {"total": 2, "completed": 1, "pending": 1, "progress": 50}


def test_chart_routes_render(client):
    user_id = _create_user(client, username="chart_user")
    _create_task(client, user_id=user_id, module="Math", assessment="A1", status=0, days=2)
    _create_task(client, user_id=user_id, module="Math", assessment="A2", status=1, days=4)
    _create_task(client, user_id=user_id, module="Physics", assessment="Lab", status=0, days=1)

    pri = client.get(f"/visualPri?name=chart_user&uid={user_id}")
    assert pri.status_code == 200
    assert b"Distribution of priority is generated" in pri.data
    assert b"chart-mobile-shell" in pri.data
    assert b"chart-canvas" in pri.data
    assert b"chart-scroll-hint" in pri.data
    assert b"data-chart-shell" in pri.data
    assert b"data-chart-hint-dismiss" in pri.data

    mod = client.get(f"/visualModule?name=chart_user&uid={user_id}")
    assert mod.status_code == 200
    assert b"Assessment distribution of each Module is generated" in mod.data
    assert b"chart-mobile-shell" in mod.data
    assert b"chart-canvas" in mod.data
    assert b"chart-scroll-hint" in mod.data
    assert b"data-chart-shell" in mod.data
    assert b"data-chart-hint-dismiss" in mod.data

    comp = client.get(f"/visualCompletion?name=chart_user&uid={user_id}")
    assert comp.status_code == 200
    assert b"Distribution of Completion is generated" in comp.data
    assert b"chart-mobile-shell" in comp.data
    assert b"chart-canvas" in comp.data
    assert b"chart-scroll-hint" in comp.data
    assert b"data-chart-shell" in comp.data
    assert b"data-chart-hint-dismiss" in comp.data


def test_dashboard_contains_touch_target_classes(client):
    user_id = _create_user(client, username="mobile_user")
    _create_task(client, user_id=user_id, module="UX", assessment="Tap Zone")

    dashboard = client.get(f"/backhome?user_id={user_id}&user_name=mobile_user")
    assert dashboard.status_code == 200
    assert b"touch-action-btn" in dashboard.data
    assert b"mobile-action-dock" in dashboard.data
    assert b"mobile.js" in dashboard.data


def test_dashboard_accessibility_hooks_present(client):
    user_id = _create_user(client, username="a11y_user")
    _create_task(client, user_id=user_id, module="Accessibility", assessment="Review")

    dashboard = client.get(f"/backhome?user_id={user_id}&user_name=a11y_user")
    assert dashboard.status_code == 200
    assert b"skip-link" in dashboard.data
    assert b"id=\"cta-help\"" in dashboard.data
    assert b"aria-describedby=\"cta-help\"" in dashboard.data
    assert b"aria-label=\"Log out account\"" in dashboard.data
    assert b"aria-label=\"Go back to home dashboard\"" in dashboard.data

    chart = client.get(f"/visualPri?name=a11y_user&uid={user_id}")
    assert chart.status_code == 200
    assert b"aria-live=\"polite\"" in chart.data
    assert b"role=\"status\"" in chart.data
    assert b"aria-atomic=\"true\"" in chart.data
    assert b"data-chart-hint-dismiss" in chart.data


def test_chart_shells_are_keyboard_accessible(client):
    user_id = _create_user(client, username="keyboard_user")
    _create_task(client, user_id=user_id, module="Keyboard", assessment="Navigation")

    chart = client.get(f"/visualModule?name=keyboard_user&uid={user_id}")
    assert chart.status_code == 200
    assert b"tabindex=\"0\"" in chart.data
    assert b"aria-describedby=\"chart-key-help\"" in chart.data
    assert b"id=\"chart-key-help\"" in chart.data


def test_no_nested_button_anchor_in_dashboard_and_edit(client):
    user_id = _create_user(client, username="semantics_user")
    task_id = _create_task(client, user_id=user_id, module="Semantics", assessment="A11y")

    dashboard = client.get(f"/backhome?user_id={user_id}&user_name=semantics_user")
    assert dashboard.status_code == 200
    assert b"<button class=\"btn btn-warning touch-action-btn\" id=\"showOverdue\"><a" not in dashboard.data
    assert b"in-task-link" in dashboard.data

    edit_page = client.get(f"/edit?edit={task_id}&host_return=semantics_user&uid_return={user_id}")
    assert edit_page.status_code == 200
    assert b"btn-link-action" in edit_page.data
    assert b"<button type=\"button\" class=\"btn btn-danger\">\n                                <a" not in edit_page.data


def test_send_reminders_sends_mail_for_today_tasks(client, monkeypatch):
    user_id = _create_user(client, username="mailer", email="mailer@example.com")

    with client.application.app_context():
        task = Task(
            module="SE",
            assessment="Presentation",
            create_date=dt.datetime.utcnow(),
            ddl=dt.datetime.now() + dt.timedelta(days=2),
            remind=dt.datetime.now() + dt.timedelta(days=1),
            description="notify",
            priority=1,
            status=0,
            host=user_id,
        )
        db.session.add(task)
        db.session.commit()

    sent = {"count": 0}

    def fake_send(_msg):
        sent["count"] += 1

    monkeypatch.setattr(mail, "send", fake_send)

    response = client.get(f"/sendReminders?user_id={user_id}&user_name=mailer")
    assert response.status_code == 200
    assert sent["count"] == 1
    assert b"Check you E-mail box for remind messages" in response.data
