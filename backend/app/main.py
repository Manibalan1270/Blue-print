from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
import os
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.endpoints.analysis import router as analysis_router
from app.services.ai_engine import get_ai_engine


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Load the embedding model at startup so the first analysis isn't slow.
    Set SKIP_MODEL_WARMUP=1 to skip (used by the tests)."""
    if os.getenv("SKIP_MODEL_WARMUP") != "1":
        get_ai_engine()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="DevPulse AI",
    description="Control room backend for intelligent development analytics.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3002").split(",")
        if o.strip()
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    print(
        f"[REQUEST] method={request.method} path={request.url.path} "
        f"duration_ms={duration_ms:.2f}"
    )
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.getLogger("devpulse").exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "code": 500},
    )


def _health() -> dict:
    return {
        "status": "online",
        "model_loaded": get_ai_engine.cache_info().currsize > 0,
        "server_time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health")
async def health_check():
    return _health()


@app.get("/api/v1/health")
async def versioned_health_check():
    return _health()


app.include_router(analysis_router, prefix="/api/v1")

