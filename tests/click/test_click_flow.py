import datetime as dt

from app import db
from app.model import Task, Todoers


def test_user_click_flow_end_to_end(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Welcome to TodoList" in response.data

    response = client.post(
        "/newAccount",
        data={
            "name": "alice",
            "mailenter": "alice@example.com",
            "psw": "Password123",
        },
    )
    assert response.status_code == 200
    assert b"registered successfully" in response.data

    response = client.post("/doList", data={"name": "alice", "psw": "Password123"})
    assert response.status_code == 200
    assert b"Welcome alice" in response.data

    with client.application.app_context():
        user = Todoers.query.filter_by(username="alice").first()
        assert user is not None
        uid = user.id

    now = dt.datetime.now()
    ddl = (now + dt.timedelta(days=3)).strftime("%Y-%m-%dT%H:%M")
    remind = (now + dt.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")

    response = client.post(
        "/createAss",
        data={
            "host": str(uid),
            "hostname": "alice",
            "moudleName": "Web Engineering",
            "ass": "Flask Portfolio Upgrade",
            "deadline": ddl,
            "remind": remind,
            "priority": "2",
        },
    )
    assert response.status_code == 200
    assert b"has been added" in response.data

    with client.application.app_context():
        task = Task.query.filter_by(host=uid, module="Web Engineering").first()
        assert task is not None
        task_id = task.taskID

    response = client.get(f"/completeTask?aim={task_id}&host=alice&uid={uid}")
    assert response.status_code == 200
    assert b"is completed" in response.data

    response = client.get(f"/edit?edit={task_id}&host_return=alice&uid_return={uid}")
    assert response.status_code == 200
    assert b"Editing task" in response.data

    response = client.post(
        "/subEdit",
        data={
            "this_task": str(task_id),
            "host": str(uid),
            "uid": "alice",
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

    response = client.post(
        "/searchStatus",
        data={"host": str(uid), "uid": "alice", "completion": "1"},
    )
    assert response.status_code == 200
    assert b"Completed Assessments" in response.data

    response = client.get(f"/searchUpcoming?user_id={uid}&user_name=alice&days=7")
    assert response.status_code == 200
    assert b"Upcoming in 7 days" in response.data

    response = client.get(f"/api/tasks?user_id={uid}")
    assert response.status_code == 200
    assert response.is_json
    assert len(response.get_json()) >= 1

    response = client.get(f"/api/summary?user_id={uid}")
    assert response.status_code == 200
    assert response.is_json
    assert "total" in response.get_json()

    response = client.get(f"/exportTasks?user_id={uid}&user_name=alice")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"

    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.is_json
    assert response.get_json().get("status") == "ok"

    response = client.get(f"/deleteTask?aim={task_id}&host=alice&uid={uid}")
    assert response.status_code == 200
    assert b"is deleted" in response.data

    with client.application.app_context():
        remaining = Task.query.filter_by(host=uid).count()
        assert remaining == 0
