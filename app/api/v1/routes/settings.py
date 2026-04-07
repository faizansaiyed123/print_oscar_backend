from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db
from app.schemas.settings import PublicSettingRead
from app.services.settings_service import SettingsService


router = APIRouter()


@router.get("/", response_model=list[PublicSettingRead])
async def get_settings(session: AsyncSession = Depends(get_db)):
    """Fetch all public store settings."""
    service = SettingsService(session)
    return await service.get_public_settings()


@router.get("/{key}", response_model=PublicSettingRead)
async def get_setting(key: str, session: AsyncSession = Depends(get_db)):
    """Fetch a specific public store setting by its key."""
    service = SettingsService(session)
    setting = await service.get_public_setting_by_key(key)
    if not setting:
        raise HTTPException(status_code=404, detail=f"Public setting '{key}' not found")
    return setting
