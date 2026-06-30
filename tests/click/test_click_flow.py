"""End-to-end flow tests for the Todo-List application."""
import datetime as dt

from app.model import Task, Todoers


def test_user_click_flow_end_to_end(client):
    """Full flow: register -> login -> create task -> complete -> edit -> search -> API."""
    # Visit landing page
    response = client.get("/")
    assert response.status_code == 200
    assert b"Welcome to TodoList" in response.data

    # Register
    response = client.post(
        "/newAccount",
        data={
            "name": "alice",
            "mailenter": "alice@example.com",
            "psw": "Password123",
        },
    )
    assert response.status_code == 200
    assert b"Registration successful" in response.data

    # Login - should redirect to dashboard
    response = client.post(
        "/doList",
        data={"name": "alice", "psw": "Password123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Welcome alice" in response.data

    # Create task
    now = dt.datetime.now()
    ddl = (now + dt.timedelta(days=3)).strftime("%Y-%m-%dT%H:%M")
    remind = (now + dt.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")

    response = client.post(
        "/createAss",
        data={
            "moudleName": "Web Engineering",
            "ass": "Flask Portfolio Upgrade",
            "deadline": ddl,
            "remind": remind,
            "priority": "2",
            "description": "Build a modern Flask app",
        },
    )
    assert response.status_code == 200
    assert b"has been added" in response.data

    with client.application.app_context():
        user = Todoers.query.filter_by(username="alice").first()
        task = Task.query.filter_by(host=user.id, module="Web Engineering").first()
        assert task is not None
        task_id = task.taskID

    # Complete task
    response = client.get(f"/completeTask?aim={task_id}")
    assert response.status_code == 200
    assert b"is completed" in response.data

    # Edit task
    response = client.get(f"/edit?edit={task_id}")
    assert response.status_code == 200
    assert b"Editing task" in response.data

    response = client.post(
        "/subEdit",
        data={
            "this_task": str(task_id),
            "create": now.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "1",
            "editmoudle": "Web Engineering",
            "editass": "Flask Portfolio Release",
            "deadline": ddl,
            "reminder": remind,
            "priority": "3",
            "descri": "Release-ready open-source package",
        },
    )
    assert response.status_code == 200
    assert b"has been updated" in response.data

    # Search by status
    response = client.post(
        "/searchStatus",
        data={"completion": "1"},
    )
    assert response.status_code == 200
    assert b"Completed Assessments" in response.data

    # Upcoming 7 days
    response = client.get("/searchUpcoming?days=7")
    assert response.status_code == 200
    assert b"Upcoming in 7 days" in response.data

    # API tasks endpoint
    response = client.get("/api/tasks")
    assert response.status_code == 200
    assert response.is_json
    tasks_payload = response.get_json()
    assert tasks_payload["total"] >= 1
    assert tasks_payload["generated_at"].endswith("Z")
    assert isinstance(tasks_payload["items"], list)

    # API summary
    response = client.get("/api/summary")
    assert response.status_code == 200
    data = response.get_json()
    assert "progress_rate" in data

    # API insights
    response = client.get("/api/insights")
    assert response.status_code == 200
    data = response.get_json()
    assert "kpis" in data
    assert "priority_distribution" in data


def test_login_required_redirects_unauthenticated(client):
    """Protected routes should redirect unauthenticated users."""
    protected_routes = ["/backhome", "/searchOverdue", "/searchUpcoming", "/api/tasks"]
    for route in protected_routes:
        response = client.get(route)
        # Flask-Login redirects to login page
        assert response.status_code == 302


def test_duplicate_user_registration_blocked(client):
    """Cannot register same username twice."""
    client.post(
        "/newAccount",
        data={"name": "dup", "mailenter": "dup@example.com", "psw": "Password123"},
    )
    response = client.post(
        "/newAccount",
        data={"name": "dup", "mailenter": "dup2@example.com", "psw": "Password123"},
    )
    assert b"has been taken" in response.data


def test_invalid_password_length_rejected(client):
    """Password shorter than 8 chars is rejected."""
    response = client.post(
        "/newAccount",
        data={"name": "shortpw", "mailenter": "s@example.com", "psw": "short"},
    )
    assert b"at least 8 characters" in response.data


def test_invalid_email_rejected(client):
    """Invalid email format is rejected."""
    response = client.post(
        "/newAccount",
        data={"name": "badmail", "mailenter": "notanemail", "psw": "Password123"},
    )
    assert b"valid email" in response.data
