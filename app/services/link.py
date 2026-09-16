import secrets
import string
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.click_event import ClickEvent
from app.models.link import Link
from app.repositories.click_event import ClickEventRepository
from app.repositories.link import LinkRepository
from app.schemas.link import LinkCreate, LinkUpdate

ALPHABET = string.ascii_letters + string.digits
SHORT_CODE_LENGTH = 7


def generate_short_code() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(SHORT_CODE_LENGTH))


class ShortCodeAlreadyExistsError(Exception):
    pass


class LinkNotAvailableError(Exception):
    pass


class LinkService:
    def __init__(self, session: AsyncSession):
        self.repository = LinkRepository(session)
        self.click_event_repository = ClickEventRepository(session)

    async def create_link(self, data: LinkCreate) -> Link:
        short_code = data.short_code

        if short_code is None:
            while True:
                short_code = generate_short_code()

                existing_link = await self.repository.get_by_short_code(short_code)

                if existing_link is None:
                    break
        else:
            existing_link = await self.repository.get_by_short_code(short_code)

            if existing_link is not None:
                raise ShortCodeAlreadyExistsError("Short code already exists")

        link = Link(
            short_code=short_code,
            destination_url=str(data.destination_url),
            expires_at=data.expires_at,
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
        return await self.repository.list_all()

    async def update_link(
        self,
        short_code: str,
        data: LinkUpdate,
    ) -> Link:
        link = await self.repository.get_by_short_code(short_code)

        if link is None:
            raise LinkNotAvailableError("Link not found")

        updates = data.model_dump(exclude_unset=True)

        for field, value in updates.items():
            setattr(link, field, value)

        return await self.repository.update(link)

    async def get_link_analytics(
        self,
        short_code: str,
    ) -> tuple[int, int, int, int]:

        link = await self.repository.get_by_short_code(short_code)

        if link is None:
            raise LinkNotAvailableError("Link not found")

        now = datetime.now(UTC)

        today_start = now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        week_start = today_start - timedelta(days=today_start.weekday())

        month_start = today_start.replace(
            day=1,
        )

        return await self.click_event_repository.get_analytics(
            link.id,
            today_start,
            week_start,
            month_start,
        )
