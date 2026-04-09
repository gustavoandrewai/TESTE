from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.services.daily_pipeline import DailyPipelineService

engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    future=True,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.create_all(engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def test_health_and_rankings():
    with TestingSessionLocal() as db:
        DailyPipelineService(db).run()

    client = TestClient(app)
    assert client.get("/health").status_code == 200
    resp = client.get("/rankings/daily")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1
