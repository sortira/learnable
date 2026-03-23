from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("LEARNABLE_DATABASE_URL", "sqlite+pysqlite:///./test_learnable.db")
os.environ.setdefault("LEARNABLE_STORAGE_ROOT", str(Path("./test-data").resolve()))

import pytest
from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app


@pytest.fixture(autouse=True)
def reset_database() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)
