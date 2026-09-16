from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.link import (
    LinkAnalyticsResponse,
    LinkCreate,
    LinkResponse,
    LinkUpdate,
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


@router.get("", response_model=list[LinkResponse])
async def list_links(
    session: AsyncSession = Depends(get_db),
) -> list[LinkResponse]:
    service = LinkService(session)
    return await service.list_links()


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
        (
            total_clicks,
            clicks_today,
            clicks_this_week,
            clicks_this_month,
        ) = await service.get_link_analytics(short_code)

    except LinkNotAvailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return LinkAnalyticsResponse(
        short_code=short_code,
        total_clicks=total_clicks,
        clicks_today=clicks_today,
        clicks_this_week=clicks_this_week,
        clicks_this_month=clicks_this_month,
    )


@router.patch(
    "/{short_code}",
    response_model=LinkResponse,
)
async def update_link(
    short_code: str,
    data: LinkUpdate,
    session: AsyncSession = Depends(get_db),
) -> LinkResponse:
    service = LinkService(session)

    try:
        updated_link = await service.update_link(short_code, data)
    except LinkNotAvailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return updated_link