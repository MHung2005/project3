import logging
import time
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError, DBAPIError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

_url = make_url(settings.DATABASE_URL)
_is_mssql = _url.get_backend_name() == "mssql"

# ── Engine ────────────────────────────────────────────────────────────────────
_engine_kwargs: dict = {"echo": settings.DEBUG, "pool_pre_ping": True}
if _is_mssql:
    # SQL Server via pyodbc: fast_executemany speeds up bulk inserts (quiz answers, options)
    _engine_kwargs.update(pool_size=10, max_overflow=20, fast_executemany=True)
elif _url.get_backend_name() == "sqlite":
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)

# ── Session Factory ───────────────────────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)


# ── Declarative Base ──────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# ── Dependency ────────────────────────────────────────────────────────────────
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a database session per request.

    Closing the session rolls back any transaction left uncommitted by a failed request.
    """
    with SessionLocal() as db:
        yield db


def _ensure_mssql_database() -> None:
    """Create the target database on SQL Server if it does not exist yet.

    The official SQL Server container only ships with system databases, so the
    application database (e.g. `elearning_db`) must be created on first boot.
    """
    db_name = _url.database
    if not db_name:
        return
    master_engine = create_engine(_url.set(database="master"), isolation_level="AUTOCOMMIT")
    try:
        with master_engine.connect() as conn:
            conn.execute(text(f"IF DB_ID(N'{db_name}') IS NULL CREATE DATABASE [{db_name}]"))
    finally:
        master_engine.dispose()


def wait_for_database() -> None:
    """Block until the database accepts connections (the DB container may still be booting)."""
    for attempt in range(1, settings.DB_CONNECT_RETRIES + 1):
        try:
            if _is_mssql:
                _ensure_mssql_database()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except (OperationalError, DBAPIError) as exc:
            if attempt == settings.DB_CONNECT_RETRIES:
                raise
            logger.warning(
                "Database not ready (attempt %s/%s): %s", attempt, settings.DB_CONNECT_RETRIES, exc.__class__.__name__
            )
            time.sleep(settings.DB_CONNECT_RETRY_DELAY)


def create_all_tables() -> None:
    """Create all tables defined in models. Call once at app startup."""
    import app.models.models  # noqa: F401 – register all models on Base.metadata

    Base.metadata.create_all(bind=engine)
