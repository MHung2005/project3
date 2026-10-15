from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_NAME: str = "ELearning Platform API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str
    DB_CONNECT_RETRIES: int = 10
    DB_CONNECT_RETRY_DELAY: float = 3.0

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    COOKIE_SECURE: bool = False  # True in production (HTTPS)

    # Initial admin account (seeded on startup if it does not exist)
    FIRST_ADMIN_EMAIL: Optional[str] = None
    FIRST_ADMIN_PASSWORD: Optional[str] = None
    FIRST_ADMIN_FULL_NAME: str = "System Administrator"

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "miniopassword2026"
    MINIO_SECURE: bool = False
    MINIO_REGION: str = "us-east-1"
    # URL the browser uses to reach MinIO (differs from MINIO_ENDPOINT inside Docker)
    MINIO_PUBLIC_URL: str = "http://localhost:9000"
    MINIO_BUCKET_MATERIALS: str = "materials"
    MINIO_BUCKET_THUMBNAILS: str = "thumbnails"
    MINIO_BUCKET_AVATARS: str = "avatars"
    MAX_UPLOAD_SIZE_MB: int = 50
    PRESIGNED_URL_EXPIRE_MINUTES: int = 60

    # Learning rules
    VIDEO_COMPLETION_THRESHOLD: float = 0.8  # >= 80% of duration
    QUIZ_SUBMIT_GRACE_SECONDS: int = 60  # network latency tolerance after time is up

    # CORS – a JSON list in the environment, e.g. ["http://localhost:3000"]
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]


settings = Settings()
