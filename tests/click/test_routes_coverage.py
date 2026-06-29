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
    assert summary["total"] == 2
    assert summary["completed"] == 1
    assert summary["pending"] == 1
    assert summary["progress"] == 50
    assert "overdue" in summary
    assert "upcoming_7_days" in summary


def test_summary_and_tasks_api_require_user_id(client):
    summary = client.get("/api/summary")
    assert summary.status_code == 400
    assert summary.get_json()["error"] == "user_id is required"

    tasks = client.get("/api/tasks")
    assert tasks.status_code == 400
    assert tasks.get_json()["error"] == "user_id is required"

    insights = client.get("/api/insights")
    assert insights.status_code == 400
    assert insights.get_json()["error"] == "user_id is required"

    timeline = client.get("/api/timeline")
    assert timeline.status_code == 400
    assert timeline.get_json()["error"] == "user_id is required"


def test_insights_and_timeline_api(client):
    user_id = _create_user(client, username="insights_user")
    _create_task(client, user_id=user_id, module="Cloud", assessment="Migrate", status=0, days=2)
    _create_task(client, user_id=user_id, module="Cloud", assessment="Deploy", status=1, days=5)
    _create_task(client, user_id=user_id, module="AI", assessment="Report", status=0, days=9)

    insights_response = client.get(f"/api/insights?user_id={user_id}")
    assert insights_response.status_code == 200
    insights = insights_response.get_json()

    assert "generated_at" in insights
    assert insights["generated_at"].endswith("Z")
    assert "kpis" in insights
    assert insights["kpis"]["total"] == 3
    assert insights["kpis"]["completed"] == 1
    assert "productivity_score" in insights["kpis"]
    assert "priority_distribution" in insights
    assert "module_distribution" in insights
    assert "module_hotspots" in insights
    assert list(insights["priority_distribution"].keys()) == ["Low", "Medium", "Significant", "Urgent"]
    assert insights["priority_distribution"]["Low"] == 0
    assert insights["priority_distribution"]["Medium"] == 3
    assert insights["priority_distribution"]["Significant"] == 0
    assert insights["priority_distribution"]["Urgent"] == 0
    assert insights["module_distribution"]["Cloud"] == 2
    assert insights["module_distribution"]["AI"] == 1
    assert insights["module_hotspots"] == [
        {"name": "Cloud", "count": 2},
        {"name": "AI", "count": 1},
    ]

    timeline_response = client.get(f"/api/timeline?user_id={user_id}&days=14")
    assert timeline_response.status_code == 200
    timeline = timeline_response.get_json()

    assert timeline["window_days"] == 14
    assert timeline["total_deadlines"] == 3
    assert isinstance(timeline["timeline"], list)
    assert len(timeline["timeline"]) == 14
    assert all("date" in item and "count" in item for item in timeline["timeline"])
    assert sum(item["count"] for item in timeline["timeline"]) == timeline["total_deadlines"]


def test_timeline_api_returns_dense_zero_filled_window(client):
    user_id = _create_user(client, username="timeline_empty")

    response = client.get(f"/api/timeline?user_id={user_id}&days=7")
    assert response.status_code == 200
    payload = response.get_json()

    assert payload["window_days"] == 7
    assert payload["total_deadlines"] == 0
    assert isinstance(payload["timeline"], list)
    assert len(payload["timeline"]) == 7
    assert all(item["count"] == 0 for item in payload["timeline"])


def test_search_overdue_scoped_to_user(client):
    user_a = _create_user(client, username="scope_a")
    user_b = _create_user(client, username="scope_b", email="scopeb@example.com")

    _create_task(client, user_id=user_a, module="A", assessment="Old A", status=0, days=-2)
    _create_task(client, user_id=user_b, module="B", assessment="Old B", status=0, days=-3)

    response = client.get(f"/searchOverdue?user_id={user_a}&user_name=scope_a")
    assert response.status_code == 200
    assert b"Old A" in response.data
    assert b"Old B" not in response.data


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
    assert b"dashboard-top" in dashboard.data
    assert b"API Docs" not in dashboard.data
    assert b"Architecture" not in dashboard.data
    assert b"Open Tasks API" not in dashboard.data
    assert b"bootstrap.min.js" not in dashboard.data
    assert b"bootstrap.js" not in dashboard.data
    assert b"Performance Intelligence Board" in dashboard.data
    assert b"data-insight-board" in dashboard.data
    assert b"insight-priority-chart" in dashboard.data
    assert b"insight-timeline-chart" in dashboard.data
    assert b"insight-trend-strip" in dashboard.data
    assert b"insight-focus-list" in dashboard.data
    assert b"Suggested Focus Today" in dashboard.data
    assert b"id=\"insight-health\"" in dashboard.data
    assert b"id=\"insight-refresh\"" in dashboard.data
    assert b"id=\"insight-summary\"" in dashboard.data
    assert b"id=\"insight-last-sync\"" in dashboard.data
    assert b"id=\"insight-module-list\"" in dashboard.data
    assert b"Module Hotspots" in dashboard.data
    assert b"id=\"insight-alert-list\"" in dashboard.data
    assert b"Risk Alerts" in dashboard.data
    assert b"insight-quick-actions" in dashboard.data
    assert b"Open Overdue Queue" in dashboard.data
    assert b"id=\"insight-heatmap\"" in dashboard.data
    assert b"Workload Heatmap" in dashboard.data


def test_login_contains_developer_zone_links(client):
    page = client.get("/newlogin")
    assert page.status_code == 200
    assert b"Portfolio Grade Flask App" in page.data
    assert b"Live Insight Board" in page.data
    assert b"Developer Zone" in page.data
    assert b"REST API Reference" in page.data
    assert b"System Architecture" in page.data
    assert b"Portfolio Docs:" not in page.data


def test_dashboard_shows_compact_empty_state_without_tasks(client):
    user_id = _create_user(client, username="empty_state_user")

    dashboard = client.get(f"/backhome?user_id={user_id}&user_name=empty_state_user")
    assert dashboard.status_code == 200
    assert b"No tasks yet. Create your first assessment from the left panel." in dashboard.data


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


def test_portfolio_css_contains_resolution_targeted_breakpoints(client):
    response = client.get("/static/css/portfolio-upgrade.css")
    assert response.status_code == 200

    css = response.data
    assert b"@media (min-width: 1000px) and (max-width: 1080px) and (max-height: 640px)" in css
    assert b"@media (min-width: 1180px) and (max-width: 1310px) and (max-height: 760px)" in css
    assert b"@media (min-width: 1320px) and (max-width: 1415px) and (max-height: 820px)" in css
    assert b"@media (min-width: 1490px) and (max-width: 1605px) and (max-height: 920px)" in css
    assert b"@media (max-height: 500px) and (max-width: 920px)" in css
    assert b"@media (min-width: 1701px)" in css
    assert b"@media (pointer: coarse) and (min-width: 900px)" in css
    assert b"@supports (padding: max(0px))" in css
    assert b"#todo_list .task-wrap:hover" in css
    assert b"#todo_list .btn-primary" in css
    assert b"#todo_list .mobile-action-dock" in css
    assert b"#todo_list .dashboard-top" in css
    assert b"#todo_list .container-fluid > .row" in css
    assert b"#todo_list .insight-health-badge" in css
    assert b"#todo_list .insight-refresh-btn" in css
    assert b"#todo_list .insight-module-list" in css
    assert b"#todo_list .insight-heatmap" in css
    assert b"#todo_list .heat-cell.lvl-4" in css
    assert b"#todo_list .left {" in css
    assert b"--space-3" in css
    assert b"#todo_list #show > h4" in css
    assert b"body:not(#todo_list):not(#gg):not(#window):not(.error-page) #form" in css
    assert b"body:not(#todo_list):not(#gg):not(#window):not(.error-page) .footer" in css
    assert b".login-box .input-group" in css
    assert b".login-box .input-btn #back" in css


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
            create_date=dt.datetime.now(),
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


def test_security_headers_exist_on_html_response(client):
    response = client.get("/newlogin")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in response.headers


def test_portfolio_api_page_has_filterable_endpoint_cards(client):
    page = client.get("/portfolio/api")
    assert page.status_code == 200
    assert b"REST API Playbook" in page.data
    assert b"id=\"endpoint-filter\"" in page.data
    assert b"data-endpoint-card" in page.data
    assert b"data-filter-category=\"all\"" in page.data
    assert b"data-filter-category=\"api\"" in page.data
    assert b"id=\"metric-total\"" in page.data
    assert b"id=\"metric-api\"" in page.data
    assert b"id=\"metric-workflow\"" in page.data
    assert b"id=\"metric-chart\"" in page.data
    assert b"id=\"filter-count\" aria-live=\"polite\"" in page.data
    assert b"Press <kbd>/</kbd> to focus search" in page.data
    assert b"Press <kbd>Esc</kbd> to clear filters" in page.data
    assert b"Press <kbd>E</kbd> to expand or collapse all cards" in page.data
    assert b"id=\"endpoint-clear\"" in page.data
    assert b"id=\"endpoint-expand\"" in page.data
    assert b"id=\"endpoint-empty\"" in page.data
    assert b"id=\"copy-feedback\"" in page.data
    assert b"Expand All" in page.data
    assert b"id=\"cat-auth\"" in page.data
    assert b"id=\"cat-api\"" in page.data
    assert b"href=\"#cat-system\"" in page.data
    assert b"data-copy-value=\"GET /api/insights?user_id=<id>\"" in page.data
    assert b"data-copy-value=\"GET /healthz\"" in page.data
    assert b"Request Recipes" in page.data
    assert b"Fetch Insights" in page.data
    assert b"curl -X GET" in page.data
    assert b"data-copy-value=\"GET /api/timeline?user_id=1&days=14\"" in page.data
    assert b"portfolio-pages.css" in page.data
    assert b"portfolio-pages.js" in page.data


def test_portfolio_architecture_page_has_dual_diagrams(client):
    page = client.get("/portfolio/architecture")
    assert page.status_code == 200
    assert b"System Architecture Blueprint" in page.data
    assert b"Component Topology" in page.data
    assert b"Runtime Request Flow" in page.data
    assert page.data.count(b'class="mermaid"') >= 2
    assert b"portfolio-pages.css" in page.data
    assert b"portfolio-pages.js" in page.data


def test_portfolio_pages_css_contains_new_toolbar_and_expand_hooks(client):
    response = client.get("/static/css/portfolio-pages.css")
    assert response.status_code == 200
    css = response.data

    assert b".toolbar-actions" in css
    assert b".clear-chip" in css
    assert b".endpoint-card.is-expanded" in css
    assert b".jump-chip" in css
    assert b".category-heading" in css
    assert b".request-recipes" in css
    assert b".recipe-grid" in css
    assert b".recipe-card" in css


def test_dashboard_home_js_supports_module_hotspots_payload(client):
    response = client.get("/static/js/home.js")
    assert response.status_code == 200
    js = response.data

    assert b"function renderModuleSpotlight(moduleDistribution, moduleHotspots)" in js
    assert b"insights.module_hotspots || []" in js
