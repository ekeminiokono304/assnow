import os
import tempfile

_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["WHATSAPP_MODE"] = "mock"
os.environ["OWNER_WHATSAPP"] = "2348061380762"
os.environ["ADMIN_PASSWORD"] = "pw"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["CRON_SECRET"] = "cron"
os.environ["WHATSAPP_APP_SECRET"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture
def admin(client):
    tok = client.post("/api/admin/login", json={"password": "pw"}).json()["token"]
    return {"Authorization": f"Bearer {tok}"}
