from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.redis import close_redis, init_redis
from app.middleware.exception_handler import register_exception_handlers
from app.middleware.request_logging import RequestLoggingMiddleware
from app.routers import health, redirect, urls

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("Starting %s in %s mode", settings.app_name, settings.app_env)
    await init_redis()
    yield
    await close_redis()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(RequestLoggingMiddleware)
    register_exception_handlers(app)

    app.include_router(health.router, prefix=settings.api_v1_prefix, tags=["health"])
    app.include_router(urls.router, prefix=settings.api_v1_prefix, tags=["urls"])
    app.include_router(redirect.router, tags=["redirect"])

    return app


app = create_app()
