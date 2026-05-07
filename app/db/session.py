from collections.abc import Generator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def enable_sqlite_foreign_keys(db_engine: Engine) -> None:
    if db_engine.dialect.name != "sqlite" and db_engine.url.get_backend_name() != "sqlite":
        return

    @event.listens_for(db_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


engine = create_engine(get_settings().database_url, pool_pre_ping=True)
enable_sqlite_foreign_keys(engine)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
