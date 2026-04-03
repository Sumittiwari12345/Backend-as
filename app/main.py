from contextlib import asynccontextmanager

from fastapi import FastAPI

from .bootstrap import initialize_database
from .config import settings
from .routers import auth, dashboard, records, users


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Backend API for finance data processing, role-based access control, "
        "and dashboard analytics."
    ),
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(records.router)
app.include_router(dashboard.router)


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "version": settings.app_version,
    }

