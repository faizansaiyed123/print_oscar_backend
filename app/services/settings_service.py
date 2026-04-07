from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.catalog import Settings
from app.models.settings import Banner


class SettingsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_public_settings(self) -> list[Settings]:
        result = await self.session.execute(select(Settings))
        return list(result.scalars().all())

    async def get_public_setting_by_key(self, key: str) -> Settings | None:
        result = await self.session.execute(
            select(Settings).where(Settings.key == key)
        )
        return result.scalar_one_or_none()

    async def get_active_banners(self) -> list[Banner]:
        result = await self.session.execute(
            select(Banner).where(Banner.is_active.is_(True)).order_by(Banner.created_at.desc())
        )
        return list(result.scalars().all())
