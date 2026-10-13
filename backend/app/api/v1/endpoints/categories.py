"""API Router – Categories."""
from fastapi import APIRouter, status

from app.api.deps import DBSession, RequireAdmin
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.schemas.user import APIResponse
from app.services.category_service import CategoryService

router = APIRouter()


@router.get("/categories", summary="Danh sách danh mục khóa học (Public)")
def get_categories(db: DBSession):
    svc = CategoryService(db)
    cats = svc.get_all()
    return APIResponse(data=cats)


@router.post("/admin/categories", status_code=status.HTTP_201_CREATED, summary="[Admin] Tạo danh mục")
def create_category(data: CategoryCreate, db: DBSession, current_user: RequireAdmin):
    svc = CategoryService(db)
    cat = svc.create(data)
    return APIResponse(message="Tạo danh mục thành công", data=cat)


@router.put("/admin/categories/{category_id}", summary="[Admin] Cập nhật danh mục")
def update_category(category_id: int, data: CategoryUpdate, db: DBSession, current_user: RequireAdmin):
    svc = CategoryService(db)
    cat = svc.update(category_id, data)
    return APIResponse(message="Cập nhật danh mục thành công", data=cat)


@router.delete("/admin/categories/{category_id}", summary="[Admin] Xóa danh mục")
def delete_category(category_id: int, db: DBSession, current_user: RequireAdmin):
    svc = CategoryService(db)
    svc.delete(category_id)
    return APIResponse(message="Xóa danh mục thành công")
