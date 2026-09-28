"""FastAPI routes for the Sentinel Chain Guardian TP/SL chart UI.

The static UI is still safety-first, but the main Sentinel Chain app now also
registers locked live-execution, streaming, and persistent drawing endpoints.
Those routes require the normal operator session/signature gates and additional
live-readiness checks before any broker call can be attempted.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

STATIC_DIR = Path(__file__).resolve().parent / "static"

router = APIRouter(prefix="/guardian", tags=["sentinel-guardian-chart"])

_ALLOWED_ASSETS = {
    "sentinel_guardian.html",
    "sentinel_guardian.css",
    "sentinel_guardian.js",
}


def _asset(name: str) -> Path:
    if name not in _ALLOWED_ASSETS:
        raise HTTPException(status_code=404, detail="Unknown Guardian UI asset")
    path = STATIC_DIR / name
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Missing Guardian UI asset: {name}")
    return path


@router.get("/health")
def guardian_health() -> dict[str, Any]:
    return {
        "ok": True,
        "module": "sentinel_chain.sentinel_guardian_routes",
        "ui": "/guardian/ui",
        "mode": "guardian_decision_support_with_locked_live_gates",
        "live_execution_routes": True,
        "live_execution_default": "locked",
        "streaming_routes": ["/guardian/ws/edge", "/guardian/ws/candles"],
        "drawing_storage_routes": ["GET/POST/DELETE /guardian/drawings"],
    }


@router.get("/ui", response_class=HTMLResponse, include_in_schema=False)
def guardian_ui() -> HTMLResponse:
    return HTMLResponse(_asset("sentinel_guardian.html").read_text(encoding="utf-8"))


@router.get("/static/{asset_name}", include_in_schema=False)
def guardian_static(asset_name: str) -> FileResponse:
    return FileResponse(_asset(asset_name))


def register_guardian_chart_routes(app: Any) -> Any:
    """Register Guardian Chart routes on a FastAPI app and return the app."""
    marker = "_sentinel_guardian_chart_routes_registered"
    if getattr(app, marker, False):
        return app
    app.include_router(router)
    setattr(app, marker, True)
    return app
