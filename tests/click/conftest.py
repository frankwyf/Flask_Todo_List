import os
from pathlib import Path

import pytest


TEST_DB_PATH = Path(__file__).resolve().parent.parent / "runtime" / "click_tests.db"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("MAIL_DEFAULT_SENDER", "noreply@example.com")

from app import app, db, bcrypt  # noqa: E402
from app.model import Todoers, Task  # noqa: E402


@pytest.fixture(scope="function")
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        db.drop_all()
        db.create_all()

    with app.test_client() as test_client:
        yield test_client

    with app.app_context():
        db.session.remove()


@pytest.fixture
def auth_client(client):
    """Provides a test client that is already logged in as 'testuser'."""
    hashed = bcrypt.generate_password_hash("Password123").decode("utf-8")
    with client.application.app_context():
        user = Todoers(username="testuser", password=hashed, Email="test@example.com", status=0)
        db.session.add(user)
        db.session.commit()

    # Log in via POST
    client.post("/doList", data={"name": "testuser", "psw": "Password123"}, follow_redirects=True)
    return client


@pytest.fixture
def sample_task(auth_client):
    """Creates a single task owned by testuser."""
    import datetime as dt

    with auth_client.application.app_context():
        user = Todoers.query.filter_by(username="testuser").first()
        task = Task(
            module="CS101",
            assessment="Final Project",
            create_date=dt.datetime.now(),
            ddl=dt.datetime.now() + dt.timedelta(days=3),
            remind=dt.datetime.now() + dt.timedelta(days=1),
            description="Build a REST API",
            priority=2,
            status=0,
            host=user.id,
        )
        db.session.add(task)
        db.session.commit()
        return {"task_id": task.taskID, "user_id": user.id}
