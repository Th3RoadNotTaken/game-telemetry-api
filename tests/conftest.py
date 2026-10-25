import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db import get_db
from app.main import app
from app.models import Base

TEST_DB_NAME = f"{settings.postgres_db}_test"

@pytest.fixture(scope="session")
def test_engine():
    admin = create_engine(settings.database_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.execute(
            text("select 1 from pg_database where datname = :name"),
            {"name": TEST_DB_NAME},
        ).scalar()
        if not exists:
            conn.execute(text(f'create database "{TEST_DB_NAME}"'))
    admin.dispose()

    engine = create_engine(make_url(settings.database_url).set(database=TEST_DB_NAME))
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()

@pytest.fixture
def client(test_engine):
    TestSession = sessionmaker(bind=test_engine)

    def override_get_db():
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    with test_engine.begin() as conn:
        conn.execute(text("truncate table events restart identity"))