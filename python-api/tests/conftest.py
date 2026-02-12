from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel

from app.database import get_engine, init_engine
from app.main import app


@pytest.fixture(autouse=True)
def isolate_database(tmp_path):
    db_file = tmp_path / "test.db"
    init_engine(f"sqlite:///{db_file}")

    SQLModel.metadata.drop_all(get_engine())
    SQLModel.metadata.create_all(get_engine())
    yield
    SQLModel.metadata.drop_all(get_engine())


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
