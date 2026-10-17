"""Repository – User data access."""
from typing import Optional

from sqlalchemy import false, true
from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email.lower()).first()

    def create(self, email: str, hashed_password: str, full_name: str, role: str = "STUDENT") -> User:
        user = User(
            email=email.lower(),
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
        is_active: Optional[bool] = None,
    ) -> tuple[list[User], int]:
        query = self.db.query(User)
        if role:
            query = query.filter(User.role == role)
        if is_active is not None:
            query = query.filter(User.is_active == (true() if is_active else false()))
        if search:
            pattern = f"%{search}%"
            query = query.filter(
                (User.full_name.ilike(pattern)) | (User.email.ilike(pattern))
            )
        total = query.count()
        # SQL Server requires ORDER BY for OFFSET/FETCH pagination
        items = query.order_by(User.id.desc()).offset((page - 1) * limit).limit(limit).all()
        return items, total
