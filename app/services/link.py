from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.click_event import ClickEvent
from app.models.link import Link
from app.repositories.click_event import ClickEventRepository
from app.repositories.link import LinkRepository
from app.schemas.link import LinkCreate


class ShortCodeAlreadyExistsError(Exception):
    pass


class LinkNotAvailableError(Exception):
    pass


class LinkService:
    def __init__(self, session: AsyncSession):
        self.repository = LinkRepository(session)
        self.click_event_repository = ClickEventRepository(session)

    async def create_link(self, data: LinkCreate) -> Link:
        existing_link = await self.repository.get_by_short_code(data.short_code)

        if existing_link is not None:
            raise ShortCodeAlreadyExistsError("Short code already exists")

        link = Link(
            short_code=data.short_code,
            destination_url=str(data.destination_url),
        )

        return await self.repository.create(link)

    async def resolve_link(self, short_code: str) -> Link:

        link = await self.repository.get_by_short_code(short_code)

        if link is None:
            raise LinkNotAvailableError("Link not found")

        if not link.is_active:
            raise LinkNotAvailableError("Link is inactive")

        if link.expires_at is not None and link.expires_at <= datetime.now(UTC):
            raise LinkNotAvailableError("Link has expired")

        return link

    async def record_click(
        self,
        link_id: int,
        ip_address: str | None = None,
        user_agent: str | None = None,
        referrer: str | None = None,
    ) -> ClickEvent:
        event = ClickEvent(
            link_id=link_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
        )

        return await self.click_event_repository.create(event)

    async def get_click_count(
        self,
        short_code: str,
    ) -> int:
        link = await self.repository.get_by_short_code(short_code)

        if link is None:
            raise LinkNotAvailableError("Link not found")

        return await self.click_event_repository.count_by_link_id(link.id)

    async def list_links(self) -> list[Link]:
        links = await self.repository.list_all()
        return links
