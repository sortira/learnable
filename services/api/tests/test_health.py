from sqlalchemy.orm import Session

from app.main import system_health


def test_health(db: Session) -> None:
    response = system_health()
    assert response["status"] == "healthy"
