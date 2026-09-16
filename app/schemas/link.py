from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl


class LinkCreate(BaseModel):
    destination_url: HttpUrl
    short_code: str | None = None
    expires_at: datetime | None = None


class LinkResponse(BaseModel):
    id: int
    short_code: str
    destination_url: HttpUrl
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class LinkAnalyticsResponse(BaseModel):
    short_code: str
    total_clicks: int
    clicks_today: int
    clicks_this_week: int
    clicks_this_month: int


class LinkUpdate(BaseModel):
    expires_at: datetime | None = None
    is_active: bool | None = None
