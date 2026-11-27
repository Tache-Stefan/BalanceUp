from fastapi import APIRouter

from app.api.routes.auth import router as auth_router

api_router = APIRouter()
api_router.include_router(auth_router)


@api_router.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Basic liveness endpoint for the API."""
    return {"status": "ok"}
