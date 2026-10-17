"""Shared column types for the ORM models.

Column types follow the data dictionary (see SDD §3.2):
- `Unicode(n)` / `UnicodeText` → NVARCHAR(n) / NVARCHAR(MAX) on SQL Server (Vietnamese text).
- `DateTime2` → DATETIME2 on SQL Server, timestamps are stored as naive UTC.
"""
from datetime import datetime

from sqlalchemy import DateTime, UnicodeText, func
from sqlalchemy.dialects.mssql import DATETIME2, NVARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from app.core.utils import utc_now

DateTime2 = DateTime().with_variant(DATETIME2(), "mssql")
# NVARCHAR(MAX) on SQL Server (never the deprecated NTEXT)
LongUnicode = UnicodeText().with_variant(NVARCHAR(None), "mssql")


def created_at_column() -> Mapped[datetime]:
    return mapped_column(DateTime2, nullable=False, default=utc_now, server_default=func.now())
