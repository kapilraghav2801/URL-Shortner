from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.link import (
    LinkAnalyticsResponse,
    LinkCreate,
    LinkResponse,
)
from app.services.link import (
    LinkNotAvailableError,
    LinkService,
    ShortCodeAlreadyExistsError,
)

router = APIRouter(
    prefix="/links",
    tags=["links"],
)


@router.post(
    "",
    response_model=LinkResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_link(
    data: LinkCreate,
    session: AsyncSession = Depends(get_db),
) -> LinkResponse:
    service = LinkService(session)

    try:
        link = await service.create_link(data)
    except ShortCodeAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return link


@router.get(
    "/{short_code}/analytics",
    response_model=LinkAnalyticsResponse,
)
async def get_link_analytics(
    short_code: str,
    session: AsyncSession = Depends(get_db),
) -> LinkAnalyticsResponse:
    service = LinkService(session)

    try:
        total_clicks = await service.get_click_count(short_code)
    except LinkNotAvailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return LinkAnalyticsResponse(
        short_code=short_code,
        total_clicks=total_clicks,
    )


@router.get("", response_model=list[LinkResponse])
async def list_links(
    session: AsyncSession = Depends(get_db),
) -> list[LinkResponse]:
    service = LinkService(session)
    links = await service.list_links()
    return links
