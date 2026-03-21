from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class SettingsUpdate(BaseModel):
    default_interval: Optional[int] = None
    max_concurrent_checks: Optional[int] = None
    request_timeout: Optional[int] = None
    default_video_count: Optional[int] = None
    site_name: Optional[str] = None
    logo_image: Optional[str] = None


class SettingsResponse(BaseModel):
    id: int
    default_interval: int
    max_concurrent_checks: int
    request_timeout: int
    default_video_count: int
    site_name: str
    logo_image: Optional[str]
    updated_at: datetime

    class Config:
        from_attributes = True
