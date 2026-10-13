"""Service – Category business logic."""
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(self, db: Session):
        self.repo = CategoryRepository(db)

    def get_all(self) -> list[Category]:
        return self.repo.get_all()

    def get_by_id(self, category_id: int) -> Category:
        cat = self.repo.get_by_id(category_id)
        if not cat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Danh mục không tồn tại.")
        return cat

    def create(self, data: CategoryCreate) -> Category:
        if self.repo.get_by_name(data.name):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tên danh mục đã tồn tại.")
        if self.repo.get_by_slug(data.slug):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slug đã được sử dụng.")
        return self.repo.create(name=data.name, slug=data.slug, description=data.description)

    def update(self, category_id: int, data: CategoryUpdate) -> Category:
        cat = self.get_by_id(category_id)
        update_data = data.model_dump(exclude_none=True)
        if "name" in update_data:
            existing = self.repo.get_by_name(update_data["name"])
            if existing and existing.id != category_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tên danh mục đã tồn tại.")
        if "slug" in update_data:
            existing = self.repo.get_by_slug(update_data["slug"])
            if existing and existing.id != category_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slug đã được sử dụng.")
        return self.repo.update(cat, **update_data)

    def delete(self, category_id: int) -> None:
        cat = self.get_by_id(category_id)
        if self.repo.has_courses(category_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể xóa danh mục đang có khóa học phụ thuộc.",
            )
        self.repo.delete(cat)
