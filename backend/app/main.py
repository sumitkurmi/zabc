"""FastAPI main application entry point for AI-Assisted Network Complaint Portal.

Specification Section 3, 4, 10.
Wires CORS, rate limiting using SlowAPI, database startup lifecycle, public and admin API routers,
background worker tasks for email outbox and auto-close, and static file serving for React frontend SPA.
"""

import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.app.config import settings
from backend.app.db import close_db_client, get_database
from backend.app.deps import verify_token
from backend.app.models import ProblemType
from backend.app.schemas import ConfigResponse, LocationOption, ProblemTypeOption
from backend.app.routers import (
    public_complaints,
    public_chat,
    admin_auth,
    admin_chats,
    admin_reference,
    network_config,
)
from backend.app.network_assets.router import router as network_assets_router

# Part 2 Imports
from backend.app.complaint_management.routers import (
    public_otp,
    student_actions,
    manager_complaints,
    leaderboard,
    technician_complaints,
    admin_staff,
    admin_junk
)
from backend.app.auth import auth_router
from backend.app.notifications.listeners import register_notification_listeners
from backend.app.notifications.service import email_outbox_worker_loop
from backend.app.complaint_management.services.auto_close_service import auto_close_worker_loop

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address, default_limits=["200/hour"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager handling startup, background loops, and shutdown events."""
    os.makedirs(settings.CHROMA_DIR, exist_ok=True)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Register event listeners
    register_notification_listeners()

    # Start background tasks
    from backend.app.agentic.worker import agent_worker_loop, stop_agent_worker
    outbox_task = asyncio.create_task(email_outbox_worker_loop())
    autoclose_task = asyncio.create_task(auto_close_worker_loop())
    agent_task = asyncio.create_task(agent_worker_loop())

    yield

    stop_agent_worker()
    agent_task.cancel()
    outbox_task.cancel()
    autoclose_task.cancel()
    close_db_client()


app = FastAPI(
    title=f"{settings.COLLEGE_NAME} AI Network Complaint Portal",
    description="REST API for AI-assisted network troubleshooting, complaint registration, and staff management",
    version="2.0.0",
    lifespan=lifespan
)

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


DEFAULT_LOCATIONS = [
    LocationOption(id="sv_patel", name="SV Patel Hostel"),
    LocationOption(id="bg_tilak", name="BG Tilak Hostel"),
    LocationOption(id="mm_malviya", name="MM Malviya Hostel"),
    LocationOption(id="pd_tandon", name="PD Tandon Hostel"),
    LocationOption(id="cv_raman", name="CV Raman Hostel"),
    LocationOption(id="rn_tagore", name="RN Tagore Hostel"),
    LocationOption(id="svbh", name="SVBH Hostel"),
    LocationOption(id="pg_hostel", name="PG Hostel"),
    LocationOption(id="sn_girls", name="SN Girls Hostel"),
    LocationOption(id="ih_b_hostel", name="IH-B Hostel"),
    LocationOption(id="kn_girls", name="KN Girls Hostel"),
    LocationOption(id="dj_girls", name="DJ Girls Hostel"),
    LocationOption(id="residential_colony", name="Residential Colony"),
    LocationOption(id="guest_house", name="Guest House"),
    LocationOption(id="academic_campus", name="Academic Campus"),
    LocationOption(id="others", name="Others")
]

PROBLEM_TYPE_OPTIONS = [
    ProblemTypeOption(value=ProblemType.LAN_PROBLEM, label="LAN PROBLEM"),
    ProblemTypeOption(value=ProblemType.IP_ADDRESS_ISSUE, label="I.P ADDRESS ISSUE"),
    ProblemTypeOption(value=ProblemType.PROXY_ISSUE, label="PROXY ISSUE"),
    ProblemTypeOption(value=ProblemType.LAN_PORT_BROKEN, label="LAN PORT BROKEN"),
    ProblemTypeOption(value=ProblemType.WIFI_PROBLEM, label="WIFI PROBLEM")
]


@app.get("/api/config", response_model=ConfigResponse, tags=["config"])
async def get_config():
    """Returns application configuration, locations, problem type labels, and allowed email domain."""
    allowed_domain = getattr(settings, "ALLOWED_EMAIL_DOMAIN", "mnnit.ac.in") or "mnnit.ac.in"
    return ConfigResponse(
        college_name=settings.COLLEGE_NAME,
        locations=DEFAULT_LOCATIONS,
        problem_types=PROBLEM_TYPE_OPTIONS,
        max_chat_messages=settings.MAX_CHAT_MESSAGES,
        max_upload_mb=settings.MAX_UPLOAD_MB,
        allowed_email_domain=allowed_domain
    )


# Include API Routers under /api prefix
app.include_router(public_complaints.router, prefix="/api")
app.include_router(public_chat.router, prefix="/api")
app.include_router(admin_auth.router, prefix="/api")
app.include_router(admin_chats.router, prefix="/api")
app.include_router(admin_reference.router, prefix="/api")
app.include_router(network_config.router, prefix="/api")
app.include_router(network_assets_router, prefix="/api")

# Include Part 2 Routers
app.include_router(public_otp.router, prefix="/api")
app.include_router(student_actions.router, prefix="/api")
app.include_router(auth_router.router, prefix="/api")
app.include_router(manager_complaints.router, prefix="/api")
app.include_router(leaderboard.router, prefix="/api")
app.include_router(technician_complaints.router, prefix="/api")
app.include_router(admin_staff.router, prefix="/api")
app.include_router(admin_junk.router, prefix="/api")


# Serve frontend static assets with server-side route guards
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend_spa(full_path: str, request: Request):
        path_str = full_path.strip("/")

        # Check if request is for admin page route (excluding admin/login and login)
        if path_str == "admin" or (path_str.startswith("admin/") and path_str != "admin/login"):
            token = request.cookies.get("admin_token") or request.cookies.get("staff_token")
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

            if not token:
                return RedirectResponse(url="/login", status_code=302)

            try:
                verify_token(token)
            except Exception:
                return RedirectResponse(url="/login", status_code=302)

        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)

        return FileResponse(os.path.join(frontend_dist, "index.html"))
