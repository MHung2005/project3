"""Service – MinIO file storage operations."""
import io
import uuid
from typing import Optional

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

ALLOWED_TYPES = {
    "materials": {"application/pdf", "application/msword",
                  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                  "application/zip", "application/x-zip-compressed"},
    "thumbnails": {"image/jpeg", "image/png", "image/webp"},
    "avatars": {"image/jpeg", "image/png", "image/webp"},
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


class StorageService:
    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self._ensure_buckets()

    def _ensure_buckets(self) -> None:
        """Create buckets if they do not exist yet."""
        for bucket in [
            settings.MINIO_BUCKET_MATERIALS,
            settings.MINIO_BUCKET_THUMBNAILS,
            settings.MINIO_BUCKET_AVATARS,
        ]:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    # Set public read policy for thumbnails and avatars
                    if bucket in (settings.MINIO_BUCKET_THUMBNAILS, settings.MINIO_BUCKET_AVATARS):
                        policy = (
                            '{"Version":"2012-10-17","Statement":[{"Effect":"Allow",'
                            '"Principal":{"AWS":["*"]},"Action":["s3:GetObject"],'
                            f'"Resource":["arn:aws:s3:::{bucket}/*"]}}]}}'
                        )
                        self.client.set_bucket_policy(bucket, policy)
            except S3Error:
                pass  # May already exist or no connection – handled gracefully

    def upload_file(
        self,
        file_data: bytes,
        content_type: str,
        original_filename: str,
        bucket: str,
    ) -> dict:
        """Upload a file to MinIO and return file info."""
        if len(file_data) > MAX_FILE_SIZE:
            raise ValueError(f"Tệp quá lớn. Giới hạn {MAX_FILE_SIZE // 1024 // 1024} MB.")

        allowed = ALLOWED_TYPES.get(bucket, set())
        if allowed and content_type not in allowed:
            raise ValueError(f"Định dạng tệp không được phép: {content_type}")

        ext = original_filename.rsplit(".", 1)[-1] if "." in original_filename else "bin"
        object_name = f"{uuid.uuid4()}.{ext}"

        self.client.put_object(
            bucket_name=bucket,
            object_name=object_name,
            data=io.BytesIO(file_data),
            length=len(file_data),
            content_type=content_type,
        )

        protocol = "https" if settings.MINIO_SECURE else "http"
        file_url = f"{protocol}://{settings.MINIO_ENDPOINT}/{bucket}/{object_name}"

        return {
            "file_url": file_url,
            "filename": original_filename,
            "file_size": len(file_data),
            "bucket": bucket,
        }

    def delete_file(self, bucket: str, object_name: str) -> None:
        """Delete a file from MinIO."""
        try:
            self.client.remove_object(bucket, object_name)
        except S3Error:
            pass


# Singleton instance
storage_service = StorageService()
