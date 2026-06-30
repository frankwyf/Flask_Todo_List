"""Unit tests for the database models."""
import datetime as dt
import os
from pathlib import Path

import pytest

TEST_DB_PATH = Path(__file__).resolve().parent.parent / "runtime" / "unit_tests.db"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("DATABASE_URL", f"sqlite:///{TEST_DB_PATH.as_posix()}")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("MAIL_DEFAULT_SENDER", "noreply@example.com")

from app import app, db, bcrypt  # noqa: E402
from app.model import Todoers, Task  # noqa: E402


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    app.config["TESTING"] = True
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield
        db.session.remove()


def test_todoers_model_creation():
    """Todoers model stores username, hashed password, and email."""
    with app.app_context():
        hashed = bcrypt.generate_password_hash("securepass").decode("utf-8")
        user = Todoers(username="modeltest", password=hashed, Email="model@test.com", status=0)
        db.session.add(user)
        db.session.commit()

        retrieved = Todoers.query.filter_by(username="modeltest").first()
        assert retrieved is not None
        assert retrieved.username == "modeltest"
        assert retrieved.Email == "model@test.com"
        assert retrieved.password != "securepass"  # hashed
        assert bcrypt.check_password_hash(retrieved.password, "securepass")


def test_todoers_repr():
    with app.app_context():
        user = Todoers(username="reprtest", password="x", Email="repr@test.com", status=1)
        db.session.add(user)
        db.session.commit()
        assert "reprtest" in repr(user)


def test_todoers_is_user_mixin():
    """Todoers inherits from UserMixin for flask-login."""
    with app.app_context():
        user = Todoers(username="mixin", password="x", Email="mixin@test.com", status=0)
        db.session.add(user)
        db.session.commit()
        assert user.is_authenticated
        assert user.is_active
        assert not user.is_anonymous


def test_task_model_creation():
    """Task model stores all fields correctly."""
    with app.app_context():
        user = Todoers(username="taskowner", password="x", Email="owner@test.com", status=0)
        db.session.add(user)
        db.session.commit()

        now = dt.datetime.now()
        task = Task(
            module="TestModule",
            assessment="TestAssessment",
            create_date=now,
            ddl=now + dt.timedelta(days=7),
            remind=now + dt.timedelta(days=3),
            description="Test description",
            priority=3,
            status=0,
            host=user.id,
        )
        db.session.add(task)
        db.session.commit()

        retrieved = Task.query.filter_by(module="TestModule").first()
        assert retrieved is not None
        assert retrieved.assessment == "TestAssessment"
        assert retrieved.priority == 3
        assert retrieved.host == user.id
        assert retrieved.status == 0
        assert retrieved.description == "Test description"


def test_task_default_values():
    """Task defaults: priority=1, status=0."""
    with app.app_context():
        user = Todoers(username="defaults", password="x", Email="def@test.com", status=0)
        db.session.add(user)
        db.session.commit()

        task = Task(
            module="Defaults",
            assessment="Check",
            create_date=dt.datetime.now(),
            host=user.id,
        )
        db.session.add(task)
        db.session.commit()

        assert task.priority == 1
        assert task.status == 0


def test_task_repr():
    with app.app_context():
        user = Todoers(username="repr2", password="x", Email="r2@test.com", status=0)
        db.session.add(user)
        db.session.commit()

        task = Task(module="Repr", assessment="Test", create_date=dt.datetime.now(), host=user.id)
        db.session.add(task)
        db.session.commit()

        r = repr(task)
        assert "Repr" in r
        assert "Test" in r


def test_username_unique_constraint():
    """Cannot create two users with same username."""
    with app.app_context():
        u1 = Todoers(username="unique", password="x", Email="u1@test.com", status=0)
        u2 = Todoers(username="unique", password="y", Email="u2@test.com", status=0)
        db.session.add(u1)
        db.session.commit()

        db.session.add(u2)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()
