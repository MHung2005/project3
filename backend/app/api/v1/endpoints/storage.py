"""API Router – File Storage (MinIO upload)."""
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.api.deps import DBSession, RequireInstructor
from app.core.config import settings
from app.schemas.user import APIResponse
from app.services.storage_service import storage_service

router = APIRouter()

VALID_BUCKETS = {
    settings.MINIO_BUCKET_MATERIALS,
    settings.MINIO_BUCKET_THUMBNAILS,
    settings.MINIO_BUCKET_AVATARS,
}


@router.post("/storage/upload", summary="[Instructor/Admin] Upload tệp lên MinIO")
async def upload_file(
    db: DBSession,
    current_user: RequireInstructor,
    file: UploadFile = File(...),
    bucket: str = Form(default="materials"),
):
    if bucket not in VALID_BUCKETS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bucket không hợp lệ. Chỉ chấp nhận: {', '.join(VALID_BUCKETS)}",
        )
    file_data = await file.read()
    content_type = file.content_type or "application/octet-stream"
    try:
        result = storage_service.upload_file(
            file_data=file_data,
            content_type=content_type,
            original_filename=file.filename or "unnamed",
            bucket=bucket,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return APIResponse(message="Upload tệp thành công", data=result)


@router.post("/storage/upload-avatar", summary="Upload ảnh đại diện (tất cả người dùng)")
async def upload_avatar(
    db: DBSession,
    current_user: RequireInstructor,  # All authenticated users can upload avatar
    file: UploadFile = File(...),
):
    file_data = await file.read()
    content_type = file.content_type or "image/jpeg"
    try:
        result = storage_service.upload_file(
            file_data=file_data,
            content_type=content_type,
            original_filename=file.filename or "avatar.jpg",
            bucket=settings.MINIO_BUCKET_AVATARS,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return APIResponse(message="Upload ảnh đại diện thành công", data=result)
