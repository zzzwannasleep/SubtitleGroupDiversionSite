from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.category import Category
from app.schemas.torrent import CategoryRead


router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
def list_categories(db: Session = Depends(get_db)) -> list[CategoryRead]:
    statement = select(Category).where(Category.is_enabled.is_(True)).order_by(Category.sort_order, Category.name)
    categories = db.scalars(statement).all()
    return [CategoryRead.model_validate(category) for category in categories]

