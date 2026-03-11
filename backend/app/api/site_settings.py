from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.site import SiteSettingsResponse
from app.services.site_settings_service import get_or_create_site_settings


router = APIRouter(prefix="/api/site-settings", tags=["site-settings"])


@router.get("", response_model=SiteSettingsResponse)
def get_site_settings(
    db: Session = Depends(get_db),
) -> SiteSettingsResponse:
    return SiteSettingsResponse.model_validate(get_or_create_site_settings(db))
