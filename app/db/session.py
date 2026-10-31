from collections.abc import Generator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings


def build_engine(database_url: str, echo: bool = False) -> Engine:
    """Create an engine. Also used by tests with an in-memory URL such as 'sqlite://'."""
    url = make_url(database_url)
    kwargs: dict = {"echo": echo}

    if url.get_backend_name() == "sqlite":
        # FastAPI serves requests from a thread pool, so allow cross-thread use.
        kwargs["connect_args"] = {"check_same_thread": False}
        if url.database in (None, "", ":memory:"):
            # One shared connection, otherwise each connection sees its own empty in-memory DB.
            kwargs["poolclass"] = StaticPool

    engine = create_engine(database_url, **kwargs)

    if url.get_backend_name() == "sqlite":
        # SQLite ignores foreign keys unless this pragma is set on every connection.
        @event.listens_for(engine, "connect")
        def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


_settings = get_settings()
engine = build_engine(_settings.database_url, echo=_settings.sql_echo)

# autoflush=False: repositories flush explicitly; services commit once per operation.
# expire_on_commit=False: objects stay readable after commit for building responses.
SessionLocal = sessionmaker(
    bind=engine, class_=Session, autoflush=False, expire_on_commit=False
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: one session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
