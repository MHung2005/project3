"""Repository – Category data access."""
from typing import Optional

from sqlalchemy.orm import Session

from app.models.models import Category


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[Category]:
        return self.db.query(Category).order_by(Category.name).all()

    def get_by_id(self, category_id: int) -> Optional[Category]:
        return self.db.query(Category).filter(Category.id == category_id).first()

    def get_by_slug(self, slug: str) -> Optional[Category]:
        return self.db.query(Category).filter(Category.slug == slug).first()

    def get_by_name(self, name: str) -> Optional[Category]:
        return self.db.query(Category).filter(Category.name == name).first()

    def create(self, name: str, slug: str, description: Optional[str] = None) -> Category:
        cat = Category(name=name, slug=slug, description=description)
        self.db.add(cat)
        self.db.commit()
        self.db.refresh(cat)
        return cat

    def update(self, category: Category, **kwargs) -> Category:
        for key, value in kwargs.items():
            if hasattr(category, key):
                setattr(category, key, value)
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete(self, category: Category) -> None:
        self.db.delete(category)
        self.db.commit()

    def has_courses(self, category_id: int) -> bool:
        from app.models.models import Course
        count = self.db.query(Course).filter(Course.category_id == category_id).count()
        return count > 0
