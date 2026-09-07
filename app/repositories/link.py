from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link import Link


class LinkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_short_code(self, short_code: str) -> Link | None:
        result = await self.session.execute(
            select(Link).where(Link.short_code == short_code)
        )

        return result.scalar_one_or_none()

    async def create(self, link: Link) -> Link:
        self.session.add(link)

        await self.session.commit()

        await self.session.refresh(link)

        return link
