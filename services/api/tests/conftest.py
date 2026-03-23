from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

os.environ.setdefault("LEARNABLE_DATABASE_URL", "sqlite+pysqlite:///./test_learnable.db")
os.environ.setdefault("LEARNABLE_STORAGE_ROOT", "./test-data")

from app.db import Base, SessionLocal, engine  # noqa: E402


API_ROOT = Path(__file__).resolve().parents[1]
TEST_DATABASE_PATH = API_ROOT / "test_learnable.db"
TEST_STORAGE_PATH = API_ROOT / "test-data"


@pytest.fixture()
def db():
    if TEST_DATABASE_PATH.exists():
        TEST_DATABASE_PATH.unlink()
    shutil.rmtree(TEST_STORAGE_PATH, ignore_errors=True)

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        if TEST_DATABASE_PATH.exists():
            TEST_DATABASE_PATH.unlink()
        shutil.rmtree(TEST_STORAGE_PATH, ignore_errors=True)
