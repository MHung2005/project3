import time

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, DBAPIError

from app.core.config import settings
from app.db.base import Base
from app.db.session import db_url, engine, is_mssql


def ensure_mssql_database() -> None:
    """Tạo database trên SQL Server nếu chưa tồn tại."""
    db_name = db_url.database
    if not db_name:
        return
    master_engine = create_engine(db_url.set(database="master"), isolation_level="AUTOCOMMIT")
    try:
        with master_engine.connect() as conn:
            conn.execute(text(f"IF DB_ID(N'{db_name}') IS NULL CREATE DATABASE [{db_name}]"))
    finally:
        master_engine.dispose()


def wait_for_database() -> None:
    """Chờ cho đến khi database chấp nhận kết nối.
    """
    for attempt in range(1, settings.DB_CONNECT_RETRIES + 1):
        try:
            if is_mssql:
                ensure_mssql_database()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except (OperationalError, DBAPIError):
            if attempt == settings.DB_CONNECT_RETRIES:
                raise
            time.sleep(settings.DB_CONNECT_RETRY_DELAY)


def create_all_tables() -> None:
    import app.models  # noqa: F401  – registers every table on Base.metadata

    Base.metadata.create_all(bind=engine)
