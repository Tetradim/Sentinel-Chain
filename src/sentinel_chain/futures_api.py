"""FastAPI routes for the Sentinel Chain futures add-on UI and planning API."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from sentinel_chain.signals import SignalValidationError, normalize_signal

from .exchanges.bitunix_futures_execution import (
    LIVE_CONFIRMATION_PHRASE,
    BitunixLiveExecutionDisabled,
    BitunixRequestError,
    BitunixFuturesTradingClient,
    load_bitunix_futures_trading_client_from_env,
)
from .exchanges.futures_native import build_native_futures_plan, dry_run_bitunix_requests

STATIC_DIR = Path(__file__).resolve().parent / "static"


def register_futures_routes(app: FastAPI) -> FastAPI:
    """Register futures UI/API routes on an existing Sentinel Chain FastAPI app."""

    state_key = "sentinel_chain_futures_routes_registered"
    if getattr(app.state, state_key, False):
        return app

    router = APIRouter(prefix="/futures", tags=["futures"])

    @router.get("/health")
    async def futures_health() -> dict[str, Any]:
        return {
            "ok": True,
            "module": "sentinel_chain.futures_api",
            "live_confirmation_phrase": LIVE_CONFIRMATION_PHRASE,
        }

    @router.get("/ui", include_in_schema=False)
    async def futures_ui() -> FileResponse:
        index_path = STATIC_DIR / "futures.html"
        if not index_path.exists():
            raise HTTPException(status_code=404, detail="futures UI asset not installed")
        return FileResponse(index_path)

    @router.post("/plan")
    async def futures_plan(request: Request) -> JSONResponse:
        body = await _json_body(request)
        signal = _signal_from_payload(body)
        plan = build_native_futures_plan(
            signal,
            venue=body.get("venue") or signal.exchange,
            mark_price=body.get("mark_price"),
            equity=body.get("equity"),
            position_id=body.get("position_id"),
            margin_mode=body.get("margin_mode", "ISOLATION"),
            margin_coin=body.get("margin_coin", "USDT"),
            trigger_price_type=body.get("trigger_price_type", "MARK_PRICE"),
            order_effect=body.get("order_effect", "GTC"),
            ccxt_capabilities=body.get("ccxt_capabilities") or {},
        )
        return JSONResponse(jsonable_encoder(plan.to_dict()))

    @router.post("/bitunix/dry-run")
    async def bitunix_dry_run(request: Request) -> JSONResponse:
        body = await _json_body(request)
        signal = _signal_from_payload(body)
        plan = build_native_futures_plan(
            signal,
            venue="bitunix",
            mark_price=body.get("mark_price"),
            equity=body.get("equity"),
            position_id=body.get("position_id"),
            margin_mode=body.get("margin_mode", "ISOLATION"),
            margin_coin=body.get("margin_coin", "USDT"),
            trigger_price_type=body.get("trigger_price_type", "MARK_PRICE"),
            order_effect=body.get("order_effect", "GTC"),
        )
        return JSONResponse(
            jsonable_encoder(
                {
                    "plan": plan.to_dict(),
                    "dry_run_requests": dry_run_bitunix_requests(plan),
                }
            )
        )

    @router.post("/bitunix/submit")
    async def bitunix_submit(request: Request) -> JSONResponse:
        body = await _json_body(request)
        confirm_live = str(body.get("confirm_live") or "")
        leg_ids = set(body.get("leg_ids") or [])
        signal = _signal_from_payload(body)
        plan = build_native_futures_plan(
            signal,
            venue="bitunix",
            mark_price=body.get("mark_price"),
            equity=body.get("equity"),
            position_id=body.get("position_id"),
            margin_mode=body.get("margin_mode", "ISOLATION"),
            margin_coin=body.get("margin_coin", "USDT"),
            trigger_price_type=body.get("trigger_price_type", "MARK_PRICE"),
            order_effect=body.get("order_effect", "GTC"),
        )
        client = _signed_client()
        submitted: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        for leg in plan.legs:
            if leg_ids and leg.id not in leg_ids:
                skipped.append({"id": leg.id, "reason": "not selected"})
                continue
            if leg.venue != "bitunix" or leg.method != "POST" or not leg.endpoint:
                skipped.append({"id": leg.id, "reason": "not a Bitunix POST leg"})
                continue
            if leg.paper_managed or leg.requires_position_id:
                skipped.append({"id": leg.id, "reason": "paper managed or requires post-fill position id"})
                continue
            if _has_placeholder(leg.body):
                skipped.append({"id": leg.id, "reason": "leg body contains placeholders"})
                continue
            try:
                result = client._mutate(  # noqa: SLF001 - route deliberately submits a validated plan leg.
                    leg.method,
                    leg.endpoint,
                    body=leg.body,
                    dry_run=False,
                    confirm_live=confirm_live,
                )
                submitted.append({"id": leg.id, "result": result.to_dict()})
            except BitunixLiveExecutionDisabled as exc:
                raise HTTPException(status_code=403, detail=str(exc)) from exc
            except BitunixRequestError as exc:
                raise HTTPException(status_code=502, detail=str(exc)) from exc
        return JSONResponse(jsonable_encoder({"plan": plan.to_dict(), "submitted": submitted, "skipped": skipped}))

    @router.get("/bitunix/funding")
    async def bitunix_funding(symbol: str = Query(..., min_length=3)) -> JSONResponse:
        client = _public_client()
        try:
            return JSONResponse(jsonable_encoder(client.get_funding_rate(symbol)))
        except BitunixRequestError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @router.get("/bitunix/positions")
    async def bitunix_positions(symbol: str | None = None) -> JSONResponse:
        client = _signed_client()
        try:
            if hasattr(client, "get_pending_positions"):
                data = client.get_pending_positions(symbol=symbol) if symbol else client.get_pending_positions()
            else:
                data = client.request_json("GET", "/api/v1/futures/position/get_pending_positions", query={}, signed=True)
            return JSONResponse(jsonable_encoder(data))
        except BitunixRequestError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @router.get("/bitunix/tpsl")
    async def bitunix_tpsl(symbol: str | None = None, position_id: str | None = None) -> JSONResponse:
        client = _signed_client()
        try:
            data = client.get_pending_tp_sl_orders(symbol=symbol, position_id=position_id)
            return JSONResponse(jsonable_encoder(data))
        except BitunixRequestError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @router.post("/bitunix/leverage")
    async def bitunix_change_leverage(request: Request) -> JSONResponse:
        body = await _json_body(request)
        client = _signed_client()
        try:
            result = client.change_leverage(
                margin_coin=body.get("margin_coin", "USDT"),
                symbol=body["symbol"],
                leverage=body["leverage"],
                dry_run=bool(body.get("dry_run", True)),
                confirm_live=str(body.get("confirm_live") or ""),
            )
            return JSONResponse(jsonable_encoder(result.to_dict()))
        except KeyError as exc:
            raise HTTPException(status_code=400, detail=f"missing field: {exc.args[0]}") from exc
        except (BitunixLiveExecutionDisabled, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except BitunixRequestError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @router.post("/bitunix/margin-mode")
    async def bitunix_change_margin_mode(request: Request) -> JSONResponse:
        body = await _json_body(request)
        client = _signed_client()
        try:
            result = client.change_margin_mode(
                margin_coin=body.get("margin_coin", "USDT"),
                symbol=body["symbol"],
                margin_mode=body["margin_mode"],
                dry_run=bool(body.get("dry_run", True)),
                confirm_live=str(body.get("confirm_live") or ""),
            )
            return JSONResponse(jsonable_encoder(result.to_dict()))
        except KeyError as exc:
            raise HTTPException(status_code=400, detail=f"missing field: {exc.args[0]}") from exc
        except (BitunixLiveExecutionDisabled, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except BitunixRequestError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    app.include_router(router)
    if STATIC_DIR.exists():
        app.mount("/futures/static", StaticFiles(directory=STATIC_DIR), name="sentinel-chain-futures-static")
    setattr(app.state, state_key, True)
    return app


async def _json_body(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="request body must be JSON") from exc
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="request body must be a JSON object")
    return body


def _signal_from_payload(body: dict[str, Any]):
    payload = body.get("signal") or body.get("alert") or body
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="signal must be an object")
    source = str(body.get("source") or payload.get("source") or "futures-ui")
    try:
        return normalize_signal(dict(payload), source=source)
    except SignalValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _public_client() -> BitunixFuturesTradingClient:
    try:
        return load_bitunix_futures_trading_client_from_env()
    except Exception:
        return BitunixFuturesTradingClient(api_key="", secret_key="")


def _signed_client() -> BitunixFuturesTradingClient:
    try:
        return load_bitunix_futures_trading_client_from_env()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Bitunix API credentials are not configured: {exc}") from exc


def _has_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return "<" in value and ">" in value
    if isinstance(value, dict):
        return any(_has_placeholder(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_has_placeholder(item) for item in value)
    return False
