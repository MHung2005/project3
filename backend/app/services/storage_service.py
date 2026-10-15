"""Service – MinIO file storage operations (SDD §4.5)."""
import io
import json
import logging
import os
import threading
import uuid
from datetime import timedelta
from typing import Optional
from urllib.parse import urlparse

from minio import Minio

from app.core.config import settings

logger = logging.getLogger(__name__)

_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
_IMAGE_EXTS = {"jpg", "jpeg", "png", "webp"}

# Accepted MIME types / extensions per bucket. A file passes if either matches,
# because browsers often send `application/octet-stream` for Office documents.
ALLOWED_TYPES = {
    settings.MINIO_BUCKET_MATERIALS: {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/zip",
        "application/x-zip-compressed",
    },
    settings.MINIO_BUCKET_THUMBNAILS: _IMAGE_TYPES,
    settings.MINIO_BUCKET_AVATARS: _IMAGE_TYPES,
}
ALLOWED_EXTENSIONS = {
    settings.MINIO_BUCKET_MATERIALS: {"pdf", "doc", "docx", "ppt", "pptx", "zip"},
    settings.MINIO_BUCKET_THUMBNAILS: _IMAGE_EXTS,
    settings.MINIO_BUCKET_AVATARS: _IMAGE_EXTS,
}
# Buckets readable anonymously by the browser; learning materials stay private
PUBLIC_BUCKETS = {settings.MINIO_BUCKET_THUMBNAILS, settings.MINIO_BUCKET_AVATARS}

MAX_FILE_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


class StorageError(Exception):
    """Raised when MinIO is unreachable or rejects an operation."""


class StorageService:
    """Thin wrapper around MinIO. The client is created lazily so the API can
    boot even when MinIO is not up yet."""

    def __init__(self):
        self._client: Optional[Minio] = None
        self._public_client: Optional[Minio] = None
        self._buckets_ready = False
        self._lock = threading.Lock()

    # ── Clients ───────────────────────────────────────────────────────────────
    @property
    def client(self) -> Minio:
        if self._client is None:
            self._client = Minio(
                endpoint=settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
                region=settings.MINIO_REGION,
            )
        return self._client

    @property
    def public_client(self) -> Minio:
        """Client bound to the public host – presigned URLs are signed for the host the browser uses."""
        if self._public_client is None:
            parsed = urlparse(settings.MINIO_PUBLIC_URL)
            self._public_client = Minio(
                endpoint=parsed.netloc,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=parsed.scheme == "https",
                region=settings.MINIO_REGION,  # fixed region → presigning needs no network call
            )
        return self._public_client

    def _ensure_buckets(self) -> None:
        if self._buckets_ready:
            return
        with self._lock:
            if self._buckets_ready:
                return
            for bucket in ALLOWED_TYPES:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                if bucket in PUBLIC_BUCKETS:
                    policy = {
                        "Version": "2012-10-17",
                        "Statement": [{
                            "Effect": "Allow",
                            "Principal": {"AWS": ["*"]},
                            "Action": ["s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{bucket}/*"],
                        }],
                    }
                    self.client.set_bucket_policy(bucket, json.dumps(policy))
            self._buckets_ready = True

    # ── Validation ────────────────────────────────────────────────────────────
    @staticmethod
    def validate(bucket: str, content_type: str, filename: str, size: int) -> str:
        """Validate a file; returns its lowercase extension. Raises ValueError."""
        if bucket not in ALLOWED_TYPES:
            raise ValueError(f"Bucket không hợp lệ. Chỉ chấp nhận: {', '.join(sorted(ALLOWED_TYPES))}")
        if size <= 0:
            raise ValueError("Tệp rỗng.")
        if size > MAX_FILE_SIZE:
            raise ValueError(f"Tệp quá lớn. Giới hạn {settings.MAX_UPLOAD_SIZE_MB} MB.")
        ext = os.path.splitext(filename)[1].lstrip(".").lower()
        if ext not in ALLOWED_EXTENSIONS[bucket]:
            raise ValueError(
                f"Định dạng tệp không được phép. Chấp nhận: {', '.join(sorted(ALLOWED_EXTENSIONS[bucket]))}"
            )
        if content_type not in ALLOWED_TYPES[bucket] and content_type != "application/octet-stream":
            raise ValueError(f"Kiểu nội dung không được phép: {content_type}")
        return ext

    # ── Operations ────────────────────────────────────────────────────────────
    def public_url(self, bucket: str, object_name: str) -> str:
        return f"{settings.MINIO_PUBLIC_URL.rstrip('/')}/{bucket}/{object_name}"

    def upload_file(self, file_data: bytes, content_type: str, original_filename: str, bucket: str) -> dict:
        """Validate and upload a file to MinIO, returning its URL and metadata."""
        ext = self.validate(bucket, content_type, original_filename, len(file_data))
        object_name = f"{uuid.uuid4().hex}.{ext}"
        try:
            self._ensure_buckets()
            self.client.put_object(
                bucket_name=bucket,
                object_name=object_name,
                data=io.BytesIO(file_data),
                length=len(file_data),
                content_type=content_type,
            )
        except Exception as exc:  # S3Error, urllib3 connection errors...
            logger.exception("MinIO upload failed")
            raise StorageError("Không thể kết nối dịch vụ lưu trữ tệp. Vui lòng thử lại sau.") from exc

        return {
            "file_url": self.public_url(bucket, object_name),
            "filename": original_filename,
            "file_size": len(file_data),
            "bucket": bucket,
            "object_name": object_name,
        }

    def parse_object_url(self, url: Optional[str]) -> Optional[tuple[str, str]]:
        """Return (bucket, object_name) when `url` points to one of our MinIO buckets."""
        if not url:
            return None
        parsed = urlparse(url)
        known_hosts = {urlparse(settings.MINIO_PUBLIC_URL).netloc, settings.MINIO_ENDPOINT}
        if parsed.netloc not in known_hosts:
            return None
        parts = parsed.path.lstrip("/").split("/", 1)
        if len(parts) != 2 or parts[0] not in ALLOWED_TYPES or not parts[1]:
            return None
        return parts[0], parts[1]

    def resolve_download_url(self, url: Optional[str]) -> Optional[str]:
        """Turn a private material URL into a short-lived presigned URL; other URLs pass through."""
        target = self.parse_object_url(url)
        if target is None or target[0] in PUBLIC_BUCKETS:
            return url
        bucket, object_name = target
        try:
            return self.public_client.presigned_get_object(
                bucket, object_name, expires=timedelta(minutes=settings.PRESIGNED_URL_EXPIRE_MINUTES)
            )
        except Exception:  # pragma: no cover – presigning is offline, but never break the page
            logger.exception("Could not presign %s", url)
            return url


# Singleton instance (no network I/O at import time)
storage_service = StorageService()
