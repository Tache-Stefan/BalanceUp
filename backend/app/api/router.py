from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Basic liveness endpoint for the API."""
    return {"status": "ok"}
