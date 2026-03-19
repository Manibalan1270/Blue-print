from datetime import datetime, timezone
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.endpoints.analysis import router as analysis_router


app = FastAPI(
    title="DevPulse AI",
    description="Control room backend for intelligent development analytics.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3002"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
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
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "code": 500},
    )


@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "model_loaded": True,
        "server_time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/v1/health")
async def versioned_health_check():
    return {
        "status": "online",
        "model_loaded": True,
        "server_time": datetime.now(timezone.utc).isoformat(),
    }


app.include_router(analysis_router, prefix="/api/v1")

print("[BOOT] DevPulse AI initialized: services loaded and router mounted at /api/v1/analyze")
