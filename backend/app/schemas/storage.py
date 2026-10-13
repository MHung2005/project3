"""Pydantic schemas – File Storage."""
from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    file_url: str
    filename: str
    file_size: int
    bucket: str
