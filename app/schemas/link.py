from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl


class LinkCreate(BaseModel):
    destination_url: HttpUrl
    short_code: str


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
