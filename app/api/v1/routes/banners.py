from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db
from app.schemas.settings import BannerRead
from app.services.settings_service import SettingsService


router = APIRouter()


@router.get("/", response_model=list[BannerRead])
async def get_banners(session: AsyncSession = Depends(get_db)):
    """Fetch all active promotional banners."""
    service = SettingsService(session)
    return await service.get_active_banners()
