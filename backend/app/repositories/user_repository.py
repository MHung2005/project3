"""Repository – User data access."""
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def create(self, email: str, hashed_password: str, full_name: str, role: str = "STUDENT") -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User, **kwargs) -> User:
        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_all_paginated(
        self,
        page: int = 1,
        limit: int = 10,
        role: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[list[User], int]:
        query = self.db.query(User)
        if role:
            query = query.filter(User.role == role)
        if search:
            pattern = f"%{search}%"
            query = query.filter(
                (User.full_name.ilike(pattern)) | (User.email.ilike(pattern))
            )
        total = query.count()
        items = query.offset((page - 1) * limit).limit(limit).all()
        return items, total
