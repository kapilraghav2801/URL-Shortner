from datetime import datetime

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

    async def get_analytics(
        self,
        link_id: int,
        today_start: datetime,
        week_start: datetime,
        month_start: datetime,
    ) -> tuple[int, int, int, int]:

        query = select(
            func.count(ClickEvent.id).label("total_clicks"),
            func.count(ClickEvent.id)
            .filter(ClickEvent.clicked_at >= today_start)
            .label("clicks_today"),
            func.count(ClickEvent.id)
            .filter(ClickEvent.clicked_at >= week_start)
            .label("clicks_this_week"),
            func.count(ClickEvent.id)
            .filter(ClickEvent.clicked_at >= month_start)
            .label("clicks_this_month"),
        ).where(ClickEvent.link_id == link_id)

        result = await self.session.execute(query)

        row = result.one()

        return (
            row.total_clicks,
            row.clicks_today,
            row.clicks_this_week,
            row.clicks_this_month,
        )
