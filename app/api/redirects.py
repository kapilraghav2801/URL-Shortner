from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.link import LinkNotAvailableError, LinkService

router = APIRouter()


@router.get("/{short_code}")
async def redirect_link(
    short_code: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    service = LinkService(session)

    try:
        link = await service.resolve_link(short_code)
    except LinkNotAvailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    await service.record_click(
        link.id,
        request.client.host,
        request.headers.get("user-agent"),
        request.headers.get("referer"),
    )

    return RedirectResponse(
        url=str(link.destination_url),
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
