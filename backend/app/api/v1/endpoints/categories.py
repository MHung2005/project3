"""API Router – Categories (SDD §5.3)."""
from fastapi import APIRouter, status

from app.api.deps import DBSession, RequireAdmin
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.schemas.common import APIResponse
from app.services.category_service import CategoryService

router = APIRouter()


@router.get("/categories", summary="Danh sách danh mục khóa học (Public)")
def get_categories(db: DBSession):
    cats = CategoryService(db).get_all()
    return APIResponse(data=[CategoryResponse.model_validate(c) for c in cats])


@router.get("/categories/{category_id}", summary="Chi tiết danh mục (Public)")
def get_category(category_id: int, db: DBSession):
    cat = CategoryService(db).get_by_id(category_id)
    return APIResponse(data=CategoryResponse.model_validate(cat))


@router.post("/admin/categories", status_code=status.HTTP_201_CREATED, summary="[Admin] Tạo danh mục")
def create_category(data: CategoryCreate, db: DBSession, current_user: RequireAdmin):
    cat = CategoryService(db).create(data)
    return APIResponse(message="Tạo danh mục thành công", data=CategoryResponse.model_validate(cat))


@router.put("/admin/categories/{category_id}", summary="[Admin] Cập nhật danh mục")
def update_category(category_id: int, data: CategoryUpdate, db: DBSession, current_user: RequireAdmin):
    cat = CategoryService(db).update(category_id, data)
    return APIResponse(message="Cập nhật danh mục thành công", data=CategoryResponse.model_validate(cat))


@router.delete("/admin/categories/{category_id}", summary="[Admin] Xóa danh mục (chặn nếu còn khóa học)")
def delete_category(category_id: int, db: DBSession, current_user: RequireAdmin):
    CategoryService(db).delete(category_id)
    return APIResponse(message="Xóa danh mục thành công")
