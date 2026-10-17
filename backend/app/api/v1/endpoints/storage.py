"""API Router – File Storage (MinIO upload, SDD §4.5, §5.7)."""
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from app.api.deps import CurrentUser, DBSession, RequireInstructor
from app.core.config import settings
from app.schemas.common import APIResponse
from app.schemas.storage import FileUploadResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.services.storage_service import MAX_FILE_SIZE, storage_service

router = APIRouter(prefix="/storage")


async def _upload(file: UploadFile, bucket: str) -> FileUploadResponse:
    if file.size is not None and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tệp quá lớn. Giới hạn {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )
    file_data = await file.read(MAX_FILE_SIZE + 1)
    # MinIO SDK is blocking – keep the event loop free
    result = await run_in_threadpool(
        storage_service.upload_file,
        file_data=file_data,
        content_type=file.content_type or "application/octet-stream",
        original_filename=file.filename or "unnamed",
        bucket=bucket,
    )
    return FileUploadResponse(**result)


@router.post("/upload", summary="[Instructor/Admin] Upload tài liệu (PDF, DOCX, PPTX, ZIP) hoặc ảnh bìa lên MinIO")
async def upload_file(
    current_user: RequireInstructor,
    file: UploadFile = File(...),
    bucket: str = Form(default=settings.MINIO_BUCKET_MATERIALS),
):
    if bucket == settings.MINIO_BUCKET_AVATARS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vui lòng dùng /storage/upload-avatar để tải ảnh đại diện.",
        )
    result = await _upload(file, bucket)
    return APIResponse(message="Upload tệp thành công", data=result)


@router.post("/upload-avatar", summary="Upload ảnh đại diện và cập nhật hồ sơ (mọi người dùng)")
async def upload_avatar(
    db: DBSession,
    current_user: CurrentUser,
    file: UploadFile = File(...),
):
    result = await _upload(file, settings.MINIO_BUCKET_AVATARS)
    user = await run_in_threadpool(AuthService(db).update_avatar, current_user, result.file_url)
    return APIResponse(
        message="Upload ảnh đại diện thành công",
        data={"file": result, "user": UserResponse.model_validate(user)},
    )
