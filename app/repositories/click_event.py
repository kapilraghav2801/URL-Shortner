from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.click_event import ClickEvent


class ClickEventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, event: ClickEvent) -> ClickEvent:
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def count_by_link_id(
        self,
        link_id: int,
    ) -> int:
        query = select(func.count(ClickEvent.id)).where(ClickEvent.link_id == link_id)

        result = await self.session.execute(query)

        return result.scalar_one()
