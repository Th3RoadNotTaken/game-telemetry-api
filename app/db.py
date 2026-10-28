from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 3},
    pool_size=20,
    max_overflow=20,
    pool_timeout=10,
)

SessionLocal = sessionmaker(bind=engine)


def get_db():
    with SessionLocal() as session:
        yield session