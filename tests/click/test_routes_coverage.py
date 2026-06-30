"""Extended coverage tests for all routes and edge cases."""
import datetime as dt
import json

from app import db
from app.model import Task, Todoers


def _create_task(client, user_id, module="Math", assessment="Quiz", status=0, days=2, priority=2):
    now = dt.datetime.now()
    with client.application.app_context():
        task = Task(
            module=module,
            assessment=assessment,
            create_date=now,
            ddl=now + dt.timedelta(days=days),
            remind=now + dt.timedelta(days=1),
            description="desc",
            priority=priority,
            status=status,
            host=user_id,
        )
        db.session.add(task)
        db.session.commit()
        return task.taskID


def test_auth_duplicate_username_guard(client):
    client.post("/newAccount", data={"name": "dup", "mailenter": "dup1@example.com", "psw": "Password123"})
    response = client.post("/newAccount", data={"name": "dup", "mailenter": "dup2@example.com", "psw": "Password123"})
    assert b"has been taken" in response.data


def test_task_post_only_endpoints_reject_get(auth_client):
    for path in ["/createAss", "/subEdit", "/searchStatus", "/searchmName", "/searchaName"]:
        response = auth_client.get(path)
        assert response.status_code == 200
        assert b"Direct URL visit is not allowed" in response.data


def test_duplicate_assessment_create_is_blocked(auth_client, sample_task):
    response = auth_client.post(
        "/createAss",
        data={
            "moudleName": "CS101",
            "ass": "Final Project",
            "deadline": (dt.datetime.now() + dt.timedelta(days=4)).strftime("%Y-%m-%dT%H:%M"),
            "remind": (dt.datetime.now() + dt.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M"),
            "priority": "2",
        },
    )
    assert response.status_code == 200
    assert b"already exists" in response.data


def test_complete_and_undo_task(auth_client, sample_task):
    tid = sample_task["task_id"]

    response = auth_client.get(f"/completeTask?aim={tid}")
    assert b"is completed" in response.data

    response = auth_client.get(f"/undoTask?aim={tid}")
    assert b"completion undone" in response.data


def test_delete_task(auth_client, sample_task):
    tid = sample_task["task_id"]
    response = auth_client.get(f"/deleteTask?aim={tid}")
    assert b"has been removed" in response.data


def test_search_module_and_assessment(auth_client, sample_task):
    response = auth_client.post("/searchmName", data={"listName": "CS101"})
    assert response.status_code == 200
    assert b"CS101" in response.data

    response = auth_client.post("/searchaName", data={"listName": "Final Project"})
    assert response.status_code == 200
    assert b"Final Project" in response.data


def test_overdue_search(auth_client):
    uid = None
    with auth_client.application.app_context():
        user = Todoers.query.filter_by(username="testuser").first()
        uid = user.id
    _create_task(auth_client, uid, module="Old", assessment="Expired", status=0, days=-5)

    response = auth_client.get("/searchOverdue")
    assert response.status_code == 200
    assert b"Overdue" in response.data


def test_export_csv(auth_client, sample_task):
    response = auth_client.get("/exportTasks")
    assert response.status_code == 200
    assert response.content_type == "text/csv; charset=utf-8"
    assert b"CS101" in response.data


def test_api_summary(auth_client, sample_task):
    response = auth_client.get("/api/summary")
    assert response.status_code == 200
    data = response.get_json()
    assert data["total"] >= 1
    assert "overdue" in data


def test_api_insights(auth_client, sample_task):
    response = auth_client.get("/api/insights")
    assert response.status_code == 200
    data = response.get_json()
    assert "kpis" in data
    assert "module_hotspots" in data


def test_api_timeline(auth_client, sample_task):
    response = auth_client.get("/api/timeline?days=7")
    assert response.status_code == 200
    data = response.get_json()
    assert data["window_days"] == 7
    assert len(data["timeline"]) == 7


def test_batch_complete(auth_client, sample_task):
    tid = sample_task["task_id"]
    response = auth_client.post(
        "/api/batch",
        data=json.dumps({"action": "complete", "task_ids": [tid]}),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["action"] == "complete"
    assert data["affected"] == 1


def test_batch_invalid_action(auth_client, sample_task):
    response = auth_client.post(
        "/api/batch",
        data=json.dumps({"action": "nope", "task_ids": [1]}),
        content_type="application/json",
    )
    assert response.status_code == 400


def test_ownership_enforcement(client, auth_client, sample_task):
    """A different user cannot complete another user's task."""
    from app import bcrypt as bc

    # Create another user and login
    hashed = bc.generate_password_hash("Password456").decode("utf-8")
    with client.application.app_context():
        user2 = Todoers(username="attacker", password=hashed, Email="evil@example.com", status=0)
        db.session.add(user2)
        db.session.commit()

    # Logout current user, login as attacker
    auth_client.get("/logout", follow_redirects=True)
    auth_client.post("/doList", data={"name": "attacker", "psw": "Password456"}, follow_redirects=True)

    tid = sample_task["task_id"]
    response = auth_client.get(f"/completeTask?aim={tid}")
    assert response.status_code == 403


def test_visualization_routes(auth_client, sample_task):
    response = auth_client.get("/visualPri")
    assert response.status_code == 200

    response = auth_client.get("/visualModule")
    assert response.status_code == 200

    response = auth_client.get("/visualCompletion")
    assert response.status_code == 200


def test_profile_change_password(auth_client):
    # GET profile page
    response = auth_client.get("/profile")
    assert response.status_code == 200
    assert b"My Profile" in response.data

    # Successful password change
    response = auth_client.post("/profile", data={
        "current_password": "Password123",
        "new_password": "NewPass1234",
        "confirm_password": "NewPass1234",
    })
    assert b"Password updated" in response.data

    # Wrong current password
    response = auth_client.post("/profile", data={
        "current_password": "WrongPass",
        "new_password": "NewPass5678",
        "confirm_password": "NewPass5678",
    })
    assert b"incorrect" in response.data


def test_logout(auth_client):
    response = auth_client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"logged out" in response.data
