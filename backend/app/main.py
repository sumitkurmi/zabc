"""FastAPI main application entry point for AI-Assisted Network Complaint Portal.

Specification Section 3, 4, 10.
Wires CORS, rate limiting using SlowAPI, database startup lifecycle, public and admin API routers,
and static file serving for React frontend SPA build.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.app.config import settings
from backend.app.db import close_db_client, get_database
from backend.app.models import ProblemType
from backend.app.schemas import ConfigResponse, LocationOption, ProblemTypeOption
from backend.app.routers import (
    public_complaints,
    public_chat,
    admin_auth,
    admin_chats,
    admin_reference,
    network_config
)

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address, default_limits=["200/hour"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager handling startup and shutdown events."""
    # Ensure data directory paths exist
    os.makedirs(settings.CHROMA_DIR, exist_ok=True)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield
    # Shutdown DB connection
    close_db_client()


app = FastAPI(
    title=f"{settings.COLLEGE_NAME} AI Network Complaint Portal",
    description="REST API for AI-assisted network troubleshooting and complaint logging",
    version="1.0.0",
    lifespan=lifespan
)

# Set rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Configurable campus locations
DEFAULT_LOCATIONS = [
    LocationOption(id="hostel_a", name="Hostel Block A"),
    LocationOption(id="hostel_b", name="Hostel Block B"),
    LocationOption(id="hostel_c", name="Hostel Block C"),
    LocationOption(id="academic", name="Academic Block"),
    LocationOption(id="library", name="Central Library"),
    LocationOption(id="labs", name="Computer Labs"),
    LocationOption(id="cafeteria", name="Cafeteria"),
    LocationOption(id="other", name="Other Campus Area")
]

# Display labels for ProblemType enum (Section 5.3)
PROBLEM_TYPE_OPTIONS = [
    ProblemTypeOption(value=ProblemType.LAN_PROBLEM, label="LAN PROBLEM"),
    ProblemTypeOption(value=ProblemType.IP_ADDRESS_ISSUE, label="I.P ADDRESS ISSUE"),
    ProblemTypeOption(value=ProblemType.PROXY_ISSUE, label="PROXY ISSUE"),
    ProblemTypeOption(value=ProblemType.LAN_PORT_BROKEN, label="LAN PORT BROKEN"),
    ProblemTypeOption(value=ProblemType.WIFI_PROBLEM, label="WIFI PROBLEM")
]


@app.get("/api/config", response_model=ConfigResponse, tags=["config"])
async def get_config():
    """Returns application configuration, locations, and problem type labels."""
    return ConfigResponse(
        college_name=settings.COLLEGE_NAME,
        locations=DEFAULT_LOCATIONS,
        problem_types=PROBLEM_TYPE_OPTIONS,
        max_chat_messages=settings.MAX_CHAT_MESSAGES,
        max_upload_mb=settings.MAX_UPLOAD_MB
    )


# Include API Routers under /api prefix
app.include_router(public_complaints.router, prefix="/api")
app.include_router(public_chat.router, prefix="/api")
app.include_router(admin_auth.router, prefix="/api")
app.include_router(admin_chats.router, prefix="/api")
app.include_router(admin_reference.router, prefix="/api")
app.include_router(network_config.router, prefix="/api")


# Serve frontend static assets if built
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend_spa(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
