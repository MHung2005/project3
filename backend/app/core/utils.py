"""Small shared helpers."""
import re
from datetime import datetime, timezone
from typing import Optional


def utc_now() -> datetime:
    """Current UTC time as a naive datetime.

    SQL Server DATETIME2 has no timezone, so every timestamp is stored as naive UTC.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


_YOUTUBE_PATTERNS = [
    re.compile(r"^(?:https?://)?(?:www\.|m\.)?youtube\.com/watch\?(?:.*&)?v=([A-Za-z0-9_-]{11})"),
    re.compile(r"^(?:https?://)?(?:www\.)?youtu\.be/([A-Za-z0-9_-]{11})"),
    re.compile(r"^(?:https?://)?(?:www\.)?youtube(?:-nocookie)?\.com/(?:embed|shorts|live)/([A-Za-z0-9_-]{11})"),
]


def extract_youtube_id(url: Optional[str]) -> Optional[str]:
    """Return the 11-character YouTube video id of a URL, or None if it is not a YouTube URL."""
    if not url:
        return None
    url = url.strip()
    for pattern in _YOUTUBE_PATTERNS:
        match = pattern.match(url)
        if match:
            return match.group(1)
    return None
