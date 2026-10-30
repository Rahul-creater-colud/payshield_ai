"""PayShield AI – FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.errors import register_error_handlers
from app.database import ensure_db

from app.routers import (
    health,
    catalog,
    risk,
    urls,
    network,
    grievances,
    dashboard,
    intelligence,
    admin,
    frontend_api,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_db()
    yield


def create_app() -> FastAPI:
    _app = FastAPI(
        title="PayShield AI",
        description=(
            "Context-aware UPI fraud prevention – hackathon MVP. "
            "All data is SYNTHETIC. Payments are SIMULATED."
        ),
        version=settings.MODEL_VERSION,
        lifespan=lifespan,
    )

    # CORS
    _app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Error handlers (must be before routers)
    register_error_handlers(_app)

    # Routers
    _app.include_router(health.router)
    _app.include_router(catalog.router)
    _app.include_router(risk.router)
    _app.include_router(urls.router)
    _app.include_router(network.router)
    _app.include_router(grievances.router)
    _app.include_router(dashboard.router)
    _app.include_router(intelligence.router)
    _app.include_router(admin.router)
    _app.include_router(frontend_api.router)

    return _app


app = create_app()
