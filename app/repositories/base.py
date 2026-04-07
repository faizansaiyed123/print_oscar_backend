from collections.abc import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def paginate(self, statement: Select, page: int = 1, page_size: int = 20):
        total_statement = select(func.count()).select_from(statement.order_by(None).subquery())
        total = await self.session.scalar(total_statement)
        result = await self.session.execute(statement.offset((page - 1) * page_size).limit(page_size))
        return result.scalars().unique().all(), int(total or 0)

    async def save(self, entity):
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def save_many(self, entities: Sequence):
        self.session.add_all(list(entities))
        await self.session.flush()
        return entities

    async def delete(self, entity) -> None:
        await self.session.delete(entity)

