"""
CampusSaarthi AI – FastAPI Application Entry Point
"""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1 import chat, documents, admin, health
from app.core.config import get_settings
from app.core.database import init_db
from app.core.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown logic."""
    logger.info("Starting CampusSaarthi AI backend…")
    await init_db()
    logger.info("Database initialized.")
    yield
    logger.info("CampusSaarthi AI backend shutting down.")


app = FastAPI(
    title="CampusSaarthi AI API",
    description="University Knowledge Assistant – RAG-powered Q&A with grounded citations.",
    version="1.0.0",
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    import uuid
    request_id = str(uuid.uuid4())
    start = time.perf_counter()
    request.state.request_id = request_id
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{elapsed:.1f}"
    logger.info(
        "request completed",
        extra={"request_id": request_id, "path": str(request.url.path),
               "method": request.method, "status": response.status_code,
               "elapsed_ms": round(elapsed, 1)},
    )
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred.", "request_id": getattr(request.state, "request_id", None)},
    )


# Routers
app.include_router(health.router, tags=["Health"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(documents.router, prefix="/api/v1", tags=["Documents"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
