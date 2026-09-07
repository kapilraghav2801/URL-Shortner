from fastapi import APIRouter

from app.api.v1.links import router as links_router

router = APIRouter(
    prefix="/api/v1",
)

router.include_router(links_router)
