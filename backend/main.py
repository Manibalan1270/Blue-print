from datetime import datetime, timezone
import time

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

APP_VERSION = "1.0.0"

app = FastAPI(
    title="DevPulse AI",
    description="Production-grade backend control room for system health and AI analysis endpoints.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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


router = APIRouter(prefix="/api/v1", tags=["Control Room"])


class RequirementAnalyzeRequest(BaseModel):
    ticket_id: str = Field(..., examples=["JIRA-123"])
    description: str = Field(..., examples=["Implement rate limiting for API gateway."])


class ContributionAnalyzeRequest(BaseModel):
    commit_hash: str = Field(..., examples=["a1b2c3d4"])
    diff: str = Field(..., examples=["+ Added retry logic in service layer"])


@router.get("/health")
async def health_check():
    return {
        "status": "online",
        "model_loaded": True,
        "server_time": datetime.now(timezone.utc).isoformat(),
        "version": APP_VERSION,
    }


@router.post("/analyze/requirement")
async def analyze_requirement(payload: RequirementAnalyzeRequest):
    return {
        "message": "Requirement analysis placeholder",
        "ticket_id": payload.ticket_id,
        "description": payload.description,
    }


@router.post("/analyze/contribution")
async def analyze_contribution(payload: ContributionAnalyzeRequest):
    return {
        "message": "Contribution analysis placeholder",
        "commit_hash": payload.commit_hash,
        "diff": payload.diff,
    }


app.include_router(router)
