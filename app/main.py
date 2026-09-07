from fastapi import FastAPI

from app.api.redirects import router as redirect_router
from app.api.v1.router import router as api_router

app = FastAPI(
    title="Link Intelligence Platform",
    version="0.1.0",
)

app.include_router(api_router)
app.include_router(redirect_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
