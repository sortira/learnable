from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

API_ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = Path(tempfile.gettempdir()) / "learnable-api-tests"
TEST_STORAGE_PATH = TEST_ROOT / "test-data"

os.environ.setdefault("LEARNABLE_DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("LEARNABLE_STORAGE_ROOT", str(TEST_STORAGE_PATH))

from app.db import Base  # noqa: E402


TEST_ENGINE = create_engine(
    "sqlite+pysqlite:///:memory:",
    future=True,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(
    bind=TEST_ENGINE,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


@pytest.fixture()
def db():
    TEST_ROOT.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(TEST_STORAGE_PATH, ignore_errors=True)

    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=TEST_ENGINE)
        shutil.rmtree(TEST_STORAGE_PATH, ignore_errors=True)
