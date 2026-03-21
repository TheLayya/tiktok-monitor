"""
MonitorSettings CRUD API endpoints
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.settings import SettingsUpdate, SettingsResponse
from app.models.monitor import MonitorSettings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["Settings"])


def get_or_create_settings(db: Session) -> MonitorSettings:
    """
    Get the singleton MonitorSettings record (id=1), creating it if it doesn't exist.
    
    **Validates: Requirements 6.1, 6.3**
    
    - Maintains unique MonitorSettings record (6.1)
    - Auto-creates default settings on init (6.3)
    """
    settings = db.query(MonitorSettings).filter(MonitorSettings.id == 1).first()
    if not settings:
        # Create default settings
        settings = MonitorSettings(
            id=1,
            default_interval=14400,  # 4 hours in seconds
            max_concurrent_checks=5,
            request_timeout=30,
            default_video_count=20,
            site_name="TikTok Monitor",
            logo_image=None
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
        logger.info("Created default MonitorSettings")
    return settings


@router.get("", response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    """
    Get current monitor settings.
    
    **Validates: Requirements 6.1, 6.3, 6.4**
    
    - Returns the unique MonitorSettings record (6.1)
    - Auto-creates default settings if not exists (6.3)
    - Provides read interface for frontend display/edit (6.4)
    """
    try:
        settings = get_or_create_settings(db)
        return settings
    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve settings"
        )


@router.put("", response_model=SettingsResponse)
def update_settings(data: SettingsUpdate, db: Session = Depends(get_db)):
    """
    Update monitor settings.
    
    **Validates: Requirements 6.1, 6.2**
    
    - Updates the unique MonitorSettings record (6.1)
    - Persists changes and takes effect next cycle (6.2)
    """
    try:
        settings = get_or_create_settings(db)
        
        # Update only provided fields
        if data.default_interval is not None:
            if data.default_interval <= 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="default_interval must be positive"
                )
            settings.default_interval = data.default_interval
        
        if data.max_concurrent_checks is not None:
            if data.max_concurrent_checks <= 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="max_concurrent_checks must be positive"
                )
            settings.max_concurrent_checks = data.max_concurrent_checks
        
        if data.request_timeout is not None:
            if data.request_timeout <= 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="request_timeout must be positive"
                )
            settings.request_timeout = data.request_timeout
        
        if data.default_video_count is not None:
            if data.default_video_count <= 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="default_video_count must be positive"
                )
            settings.default_video_count = data.default_video_count
        
        if data.site_name is not None:
            settings.site_name = data.site_name
        
        # Allow clearing logo by passing empty string or None
        if data.logo_image is not None:
            settings.logo_image = data.logo_image if data.logo_image else None
        
        db.commit()
        db.refresh(settings)
        logger.info(f"Updated MonitorSettings: {settings.id}")
        return settings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update settings: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update settings"
        )
