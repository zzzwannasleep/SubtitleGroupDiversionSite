from sqlalchemy.orm import Session

from app.models.site_settings import SiteSettings


DEFAULT_SITE_NAME = "PT Platform"
SITE_SETTINGS_PRIMARY_KEY = 1


def get_or_create_site_settings(db: Session) -> SiteSettings:
    site_settings = db.get(SiteSettings, SITE_SETTINGS_PRIMARY_KEY)
    if site_settings is not None:
        return site_settings

    site_settings = SiteSettings(id=SITE_SETTINGS_PRIMARY_KEY, site_name=DEFAULT_SITE_NAME)
    db.add(site_settings)
    db.commit()
    db.refresh(site_settings)
    return site_settings
