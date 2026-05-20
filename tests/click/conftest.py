import os
from pathlib import Path

import pytest


TEST_DB_PATH = Path(__file__).resolve().parent.parent / "runtime" / "click_tests.db"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("MAIL_DEFAULT_SENDER", "noreply@example.com")

from app import app, db  # noqa: E402


@pytest.fixture(scope="function")
def client():
    app.config["TESTING"] = True

    with app.app_context():
        db.drop_all()
        db.create_all()

    with app.test_client() as test_client:
        yield test_client

    with app.app_context():
        db.session.remove()
