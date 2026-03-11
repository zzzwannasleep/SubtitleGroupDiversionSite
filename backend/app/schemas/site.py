from pydantic import BaseModel, ConfigDict, Field


class SiteSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    site_name: str


class SiteSettingsUpdateRequest(BaseModel):
    site_name: str = Field(min_length=1, max_length=120)
