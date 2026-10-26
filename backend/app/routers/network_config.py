
"""Download OS-specific network configuration scripts for C Block."""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

router = APIRouter(
    prefix="/network-config",
    tags=["network configuration"],
)

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts"

SCRIPT_CONFIG = {
    "linux": {
        "path": SCRIPTS_DIR / "configure_hostel_network.py",
        "filename": "configure_hostel_network.py",
        "media_type": "text/x-python",
    },
    "ubuntu": {
        "path": SCRIPTS_DIR / "configure_hostel_network.py",
        "filename": "configure_hostel_network.py",
        "media_type": "text/x-python",
    },
    "windows": {
        "path": SCRIPTS_DIR / "configure_hostel_network.ps1",
        "filename": "configure_hostel_network.ps1",
        "media_type": "text/plain",
    },
}


@router.get("/download")
async def download_network_script(
    os_name: str = Query(default="linux"),
):
    selected_os = os_name.strip().lower()

    if selected_os not in SCRIPT_CONFIG:
        raise HTTPException(
            status_code=400,
            detail="Unsupported OS. Choose 'linux', 'ubuntu', or 'windows'.",
        )

    script = SCRIPT_CONFIG[selected_os]

    if not script["path"].is_file():
        raise HTTPException(
            status_code=500,
            detail=f"The {selected_os} configuration script is not installed on the server.",
        )

    return FileResponse(
        path=script["path"],
        media_type=script["media_type"],
        filename=script["filename"],
    )
