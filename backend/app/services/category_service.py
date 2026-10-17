"""Service – Category business logic."""
from sqlalchemy.orm import Session

from app.models import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.core.exceptions import BadRequestError, NotFoundError


class CategoryService:
    def __init__(self, db: Session):
        self.repo = CategoryRepository(db)

    def get_all(self) -> list[Category]:
        return self.repo.get_all()

    def get_by_id(self, category_id: int) -> Category:
        cat = self.repo.get_by_id(category_id)
        if not cat:
            raise NotFoundError("Danh mục không tồn tại.")
        return cat

    def _ensure_unique(self, name: str | None, slug: str | None, category_id: int | None = None) -> None:
        """Name and slug must not belong to another category."""
        existing = name and self.repo.get_by_name(name)
        if existing and existing.id != category_id:
            raise BadRequestError("Tên danh mục đã tồn tại.")
        existing = slug and self.repo.get_by_slug(slug)
        if existing and existing.id != category_id:
            raise BadRequestError("Slug đã được sử dụng.")

    def create(self, data: CategoryCreate) -> Category:
        self._ensure_unique(data.name, data.slug)
        return self.repo.create(name=data.name, slug=data.slug, description=data.description)

    def update(self, category_id: int, data: CategoryUpdate) -> Category:
        cat = self.get_by_id(category_id)
        self._ensure_unique(data.name, data.slug, category_id)
        return self.repo.update(cat, **data.model_dump(exclude_none=True))

    def delete(self, category_id: int) -> None:
        cat = self.get_by_id(category_id)
        if self.repo.has_courses(category_id):
            raise BadRequestError("Không thể xóa danh mục đang có khóa học phụ thuộc.")
        self.repo.delete(cat)
