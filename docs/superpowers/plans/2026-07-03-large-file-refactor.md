# Large File Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce the highest-risk large files into focused modules without changing runtime behavior, safety gates, paper execution semantics, or public API contracts.

**Architecture:** Start with characterization tests and pure-helper extraction, then split route groups behind registrar functions, then split UI JavaScript into browser-loaded modules. Keep compatibility imports where existing tests or users may import from old files.

**Tech Stack:** FastAPI, pytest, Starlette TestClient, plain browser JavaScript, Node syntax checks, optional Playwright smoke scripts.

---

## Current Hotspots

Measured from the working tree on 2026-07-03:

- `src/sentinel_chain/app.py`: 4006 lines. Contains app factory, security helpers, Guardian routes, exchange routes, market routes, bracket routes, signals, backtests, serializers, parsing helpers, and addon wrappers.
- `src/sentinel_chain/static/sentinel_guardian.js`: 2382 lines. Contains embedded sample data, chart rendering, state, API client, UI rendering, trading actions, streams, and event wiring in one IIFE.
- `src/sentinel_chain/static/app.js`: 1934 lines. Main operator UI, already depends on `api.js`, `formatters.js`, `storage.js`, and `catalog.js`, so it is easier to split.
- `src/sentinel_chain/execution.py`: 1887 lines. Contains execution models, `PaperExchange`, fill logic, bracket amendments, trailing logic, order serialization, and exit builders.
- `src/sentinel_chain/charting/automap.py`: 1571 lines. Contains candle normalization, indicators, pivots, levels, chart patterns, trade plans, scoring, demo data, and backtesting.

## File Structure Target

### Backend API

- Keep: `src/sentinel_chain/app.py`
  - Responsibility after refactor: create app objects, assemble dependencies, register route modules.
  - Target size: under 700 lines after the route split.
- Create: `src/sentinel_chain/api/parsing.py`
  - Decimal/date/candle/backtest payload parsing helpers.
- Create: `src/sentinel_chain/api/serializers.py`
  - Account, risk, signal, preview, and bracket plan response serializers.
- Create: `src/sentinel_chain/api/context.py`
  - Dataclass for route registrars that need shared app services.
- Create: `src/sentinel_chain/brackets/views.py`
  - Bracket response builders, ladder rows, decision support rows, health, OCA, and totals.
- Create: `src/sentinel_chain/guardian/state.py`
  - Guardian runtime storage, drawing validation, Edge payload normalization, preview key helpers.
- Create: `src/sentinel_chain/guardian/api.py`
  - Guardian drawings, Edge, candles websocket, live status, live preview, live submit.
- Create: `src/sentinel_chain/exchanges/api.py`
  - Exchange catalog, CCXT, Bitunix public/private routes.
- Create: `src/sentinel_chain/brackets/api.py`
  - Bracket status, preview, amendments, close/cancel, risk summary.
- Create: `src/sentinel_chain/signals/api.py`
  - Signals, approvals, templates, strategy presets.
- Create: `src/sentinel_chain/backtests/api.py`
  - Signal, candle, batch, stress backtest routes.

### Execution

- Keep: `src/sentinel_chain/execution.py`
  - Compatibility re-export surface.
- Create: `src/sentinel_chain/execution_models.py`
  - `ExitOrder`, `ExecutionCostConfig`, `PaperLot`, `PaperPosition`, `PaperOrder`, `ExecutionResult`.
- Create: `src/sentinel_chain/paper_exchange.py`
  - `PaperExchange` and fill/replay methods.
- Create: `src/sentinel_chain/exit_orders.py`
  - `build_exit_orders`, amendment helpers, trailing helpers, serialization helpers.

### Charting

- Keep: `src/sentinel_chain/charting/automap.py`
  - Orchestrator/re-export module.
- Create: `src/sentinel_chain/charting/candles.py`
- Create: `src/sentinel_chain/charting/indicators.py`
- Create: `src/sentinel_chain/charting/levels.py`
- Create: `src/sentinel_chain/charting/patterns.py`
- Create: `src/sentinel_chain/charting/trade_plans.py`
- Create: `src/sentinel_chain/charting/demo.py`

### Guardian UI

- Keep: `src/sentinel_chain/static/sentinel_guardian.js`
  - Final bootstrap/event wiring file.
- Create: `src/sentinel_chain/static/sentinel_guardian_sample.js`
  - `window.SentinelGuardianSample.edgeHeatmapSample` contains the existing Edge heatmap sample object moved verbatim from `sentinel_guardian.js`.
- Create: `src/sentinel_chain/static/sentinel_guardian_core.js`
  - DOM helpers, state, formatting, API helpers, local storage helpers.
- Create: `src/sentinel_chain/static/sentinel_guardian_chart.js`
  - Candle generation, indicators, chart bounds, rendering, pointer interactions.
- Create: `src/sentinel_chain/static/sentinel_guardian_panels.js`
  - Panel rendering for dashboard, risk, VCP, drawings, portfolio, strategies, exchanges, war room, audit, data.
- Create: `src/sentinel_chain/static/sentinel_guardian_trading.js`
  - Signal parsing, ticket building, buy/sell preview/submit, live preview/blocked submit, bracket actions.
- Create: `src/sentinel_chain/static/sentinel_guardian_streams.js`
  - Edge/candle websocket and drawing persistence calls.

---

## Task 1: Add Characterization Tests Before Moving Code

**Files:**
- Create: `tests/test_route_contracts.py`
- Create: `tests/test_guardian_static_contract.py`

- [ ] **Step 1: Add route inventory contract tests**

Create `tests/test_route_contracts.py`:

```python
from fastapi.testclient import TestClient

from sentinel_chain.app import create_app


def test_core_route_contracts_survive_refactors():
    client = TestClient(create_app())
    expected = [
        ("GET", "/health"),
        ("GET", "/ui/state"),
        ("GET", "/guardian/health"),
        ("GET", "/guardian/ui"),
        ("GET", "/war-room/features"),
        ("GET", "/exchanges"),
        ("GET", "/exchanges/platforms"),
        ("GET", "/exchanges/ccxt/catalog"),
        ("GET", "/brackets"),
        ("GET", "/brackets/risk-summary"),
        ("GET", "/signals"),
        ("GET", "/approvals"),
        ("GET", "/audit"),
    ]
    for method, path in expected:
        response = client.request(method, path)
        assert response.status_code == 200, (method, path, response.text)


def test_mutating_routes_keep_expected_validation_behavior():
    client = TestClient(create_app())
    preview = client.post(
        "/signals/preview",
        json={
            "symbol": "BTCUSDT",
            "side": "buy",
            "exchange": "paper",
            "market_type": "swap",
            "quote_amount": "25",
            "price": "65000",
            "stop_loss_price": "64000",
        },
    )
    assert preview.status_code == 200
    body = preview.json()
    assert "accepted" in body
    assert "risk" in body
```

- [ ] **Step 2: Add Guardian static contract tests**

Create `tests/test_guardian_static_contract.py`:

```python
from fastapi.testclient import TestClient

from sentinel_chain.app import create_app


def test_guardian_static_assets_are_browser_loadable():
    client = TestClient(create_app())
    ui = client.get("/guardian/ui")
    assert ui.status_code == 200
    assert "sentinel_guardian.css" in ui.text
    assert "sentinel_guardian.js" in ui.text

    for asset in [
        "sentinel_guardian.css",
        "sentinel_guardian.js",
    ]:
        response = client.get(f"/guardian/static/{asset}")
        assert response.status_code == 200
        assert response.text


def test_guardian_script_contains_required_ui_hooks():
    client = TestClient(create_app())
    script = client.get("/guardian/static/sentinel_guardian.js").text
    required_hooks = [
        "previewLiveOrderFromTicket",
        "submitLiveOrderFromPreview",
        "startCandleStream",
        "startEdgeStream",
        "saveServerDrawings",
        "loadVenueJson",
    ]
    for hook in required_hooks:
        assert hook in script
```

- [ ] **Step 3: Run the characterization tests**

Run:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests\test_route_contracts.py tests\test_guardian_static_contract.py -q
```

Expected: both new test files pass.

- [ ] **Step 4: Run existing focused suites**

Run:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests\test_app.py tests\test_operator_ui.py tests\test_guardian_chart_ui.py tests\test_guardian_live_wiring.py tests\test_market_streaming.py tests\test_ccxt_brokerage_wiring.py -q
```

Expected: pass with only the existing Starlette deprecation warning.

- [ ] **Step 5: Commit**

```powershell
git add tests\test_route_contracts.py tests\test_guardian_static_contract.py
git commit -m "test: lock route and guardian static contracts"
```

---

## Task 2: Extract App Parsing Helpers

**Files:**
- Create: `src/sentinel_chain/api/__init__.py`
- Create: `src/sentinel_chain/api/parsing.py`
- Modify: `src/sentinel_chain/app.py`
- Test: `tests/test_api_parsing.py`

- [ ] **Step 1: Add direct helper tests**

Create `tests/test_api_parsing.py`:

```python
from decimal import Decimal

import pytest

from sentinel_chain.api.parsing import candle_payload, positive_decimal


def test_positive_decimal_accepts_positive_numeric_strings():
    assert positive_decimal("1.25") == Decimal("1.25")


def test_positive_decimal_rejects_zero_and_negative_values():
    with pytest.raises(ValueError):
        positive_decimal("0")
    with pytest.raises(ValueError):
        positive_decimal("-1")


def test_candle_payload_normalizes_ohlcv_payloads():
    candle = candle_payload(
        {"time": "T1", "open": "10", "high": "12", "low": "9", "close": "11", "volume": "100"}
    )
    assert candle == {
        "time": "T1",
        "open": Decimal("10"),
        "high": Decimal("12"),
        "low": Decimal("9"),
        "close": Decimal("11"),
        "volume": Decimal("100"),
    }
```

- [ ] **Step 2: Verify the tests fail before extraction**

Run:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests\test_api_parsing.py -q
```

Expected: fail with `ModuleNotFoundError: No module named 'sentinel_chain.api'`.

- [ ] **Step 3: Create `api/parsing.py` with public names**

Move these functions from `src/sentinel_chain/app.py` into `src/sentinel_chain/api/parsing.py`, renaming by removing the leading underscore:

- `_positive_decimal` -> `positive_decimal`
- `_optional_positive_decimal` -> `optional_positive_decimal`
- `_optional_datetime` -> `optional_datetime`
- `_truthy` -> `truthy`
- `_non_negative_int` -> `non_negative_int`
- `_optional_int` -> `optional_int`
- `_non_negative_decimal` -> `non_negative_decimal`
- `_decimal` -> `decimal_value`
- `_candle_payload` -> `candle_payload`
- `_stress_scenario_payload` -> `stress_scenario_payload`
- `_batch_backtest_candidate_payload` -> `batch_backtest_candidate_payload`
- `_execution_cost_payload` -> `execution_cost_payload`
- `_bitunix_kline_query` -> `bitunix_kline_query`

Keep compatibility aliases in `app.py` during this task:

```python
from .api.parsing import (
    batch_backtest_candidate_payload as _batch_backtest_candidate_payload,
    bitunix_kline_query as _bitunix_kline_query,
    candle_payload as _candle_payload,
    decimal_value as _decimal,
    execution_cost_payload as _execution_cost_payload,
    non_negative_decimal as _non_negative_decimal,
    non_negative_int as _non_negative_int,
    optional_datetime as _optional_datetime,
    optional_int as _optional_int,
    optional_positive_decimal as _optional_positive_decimal,
    positive_decimal as _positive_decimal,
    stress_scenario_payload as _stress_scenario_payload,
    truthy as _truthy,
)
```

- [ ] **Step 4: Delete the moved helper bodies from `app.py`**

Remove the original function definitions from `src/sentinel_chain/app.py` after aliases are imported. Do not change call sites yet.

- [ ] **Step 5: Run focused tests**

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests\test_api_parsing.py tests\test_app.py tests\test_backtest.py -q
```

Expected: pass.

- [ ] **Step 6: Commit**

```powershell
git add src\sentinel_chain\api\__init__.py src\sentinel_chain\api\parsing.py src\sentinel_chain\app.py tests\test_api_parsing.py
git commit -m "refactor: extract api parsing helpers"
```

---

## Task 3: Extract API Serializers

**Files:**
- Create: `src/sentinel_chain/api/serializers.py`
- Modify: `src/sentinel_chain/app.py`
- Test: `tests/test_api_serializers.py`

- [ ] **Step 1: Add serializer tests**

Create `tests/test_api_serializers.py`:

```python
from decimal import Decimal

from sentinel_chain.api.serializers import decimal_to_plain


def test_decimal_to_plain_strips_scientific_notation():
    assert decimal_to_plain(Decimal("1E-8")) == "0.00000001"
    assert decimal_to_plain(Decimal("100.00000000")) == "100.00000000"
```

- [ ] **Step 2: Verify the tests fail before extraction**

Run:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests\test_api_serializers.py -q
```

Expected: fail because `sentinel_chain.api.serializers` does not exist.

- [ ] **Step 3: Move serializer helpers**

Move these helpers from `src/sentinel_chain/app.py` to `src/sentinel_chain/api/serializers.py`:

- `_risk_config_to_dict`
- `_account_state_to_dict`
- `_signal_to_dict`
- `_risk_decision_to_dict`
- `_signal_preview`
- `_bracket_plan_to_dict`
- `_worst_case_loss`
- `_target_reward`
- `_total_target_reward`
- `_decimal_to_plain` -> public `decimal_to_plain`
- `_money`

Keep compatibility aliases in `app.py` for one commit:

```python
from .api.serializers import (
    account_state_to_dict as _account_state_to_dict,
    bracket_plan_to_dict as _bracket_plan_to_dict,
    decimal_to_plain as _decimal_to_plain,
    money as _money,
    risk_config_to_dict as _risk_config_to_dict,
    risk_decision_to_dict as _risk_decision_to_dict,
    signal_preview as _signal_preview,
    signal_to_dict as _signal_to_dict,
    target_reward as _target_reward,
    total_target_reward as _total_target_reward,
    worst_case_loss as _worst_case_loss,
)
```

- [ ] **Step 4: Run focused tests**

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests\test_api_serializers.py tests\test_operator_ui.py tests\test_app.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```powershell
git add src\sentinel_chain\api\serializers.py src\sentinel_chain\app.py tests\test_api_serializers.py
git commit -m "refactor: extract api serializers"
```

---

## Task 4: Extract Bracket View Builders

**Files:**
- Create: `src/sentinel_chain/brackets/views.py`
- Modify: `src/sentinel_chain/app.py`
- Test: existing `tests/test_app.py`, `tests/test_market_price_api.py`

- [ ] **Step 1: Move bracket response helpers**

Move these helpers from `src/sentinel_chain/app.py` to `src/sentinel_chain/brackets/views.py`:

- `_active_exits_to_dict`
- `_active_exit_to_dict`
- `_active_brackets_to_dict`
- `_bracket_exit_ladder_to_dict`
- `_bracket_decision_support_to_dict`
- `_bracket_coverage_to_dict`
- `_decision_support_row`
- `_exit_ladder_row`
- `_trailing_telemetry`
- `_trailing_activation_ready`
- `_candidate_trailing_trigger`
- `_trailing_distance`
- `_trailing_step_required`
- `_bracket_risk_summary`
- `_bracket_health`
- `_bracket_health_row`
- `_bracket_oca_groups`
- `_oca_conflict_signal_ids`
- `_lot_oca_groups`
- `_empty_bracket_totals`
- `_accumulate_bracket_totals`
- `_bracket_totals_to_dict`
- `_decimal_or_zero`
- `_decimal_or_none`
- `_bracket_summary`
- `_nearest_protective_exit`
- `_nearest_take_profit_exit`
- `_lot_protective_loss`
- `_lot_protective_locked_pnl`
- `_lot_protective_distance_pct`
- `_lot_target_reward`
- `_lot_total_target_reward`

Use the same compatibility alias pattern as Tasks 2 and 3. Do not rewrite route functions yet.

- [ ] **Step 2: Run bracket-focused tests**

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests\test_app.py tests\test_market_price_api.py -q
```

Expected: pass.

- [ ] **Step 3: Commit**

```powershell
git add src\sentinel_chain\brackets\views.py src\sentinel_chain\app.py
git commit -m "refactor: extract bracket view builders"
```

---

## Task 5: Extract Guardian Runtime State

**Files:**
- Create: `src/sentinel_chain/guardian/__init__.py`
- Create: `src/sentinel_chain/guardian/state.py`
- Modify: `src/sentinel_chain/app.py`
- Test: `tests/test_guardian_state.py`, existing `tests/test_guardian_live_wiring.py`

- [ ] **Step 1: Add Guardian state tests**

Create `tests/test_guardian_state.py`:

```python
from sentinel_chain.guardian.state import GuardianRuntimeStore


def test_guardian_runtime_store_validates_and_round_trips_drawings():
    store = GuardianRuntimeStore(repository=None)
    saved = store.save_drawings(
        "btcusdt",
        [{"type": "hline", "price": 65000, "label": "support"}],
    )
    assert saved["symbol"] == "BTCUSDT"
    assert saved["count"] == 1

    loaded = store.load_drawings("BTCUSDT")
    assert loaded["drawings"][0]["type"] == "hline"

    deleted = store.delete_drawings("BTCUSDT")
    assert deleted["deleted"] is True


def test_guardian_runtime_store_rejects_too_many_drawings():
    store = GuardianRuntimeStore(repository=None)
    too_many = [{"type": "hline", "price": i} for i in range(501)]
    try:
        store.save_drawings("BTCUSDT", too_many)
    except ValueError as exc:
        assert "limited to 500" in str(exc)
    else:
        raise AssertionError("expected ValueError")
```

- [ ] **Step 2: Create the store class**

Move these behaviors from `app.py` into `src/sentinel_chain/guardian/state.py`:

- `_guardian_key`
- `_guardian_symbol`
- `_runtime_get`
- `_runtime_set`
- `_runtime_delete`
- `_runtime_list`
- `_now_iso`
- `_drawing_payload`
- `_validate_drawings`
- `_edge_snapshot_payload`
- `_live_preview_key`
- `_live_order_key`
- `_ccxt_preview_key`
- `_ccxt_order_key`

Use this public API:

- `GuardianRuntimeStore(repository)` initializes the same in-memory buckets currently assigned to `guardian_memory`.
- `load_drawings(symbol: str = "BTCUSDT") -> dict` returns the same payload shape as the current `GET /guardian/drawings` route.
- `save_drawings(symbol: str, drawings: list[dict]) -> dict` validates drawing count and object shape, persists through runtime state when a repository exists, and returns the same payload shape as the current `POST /guardian/drawings` route.
- `delete_drawings(symbol: str = "BTCUSDT") -> dict` deletes both in-memory and repository-backed drawing records.
- `edge_snapshot(payload: dict) -> dict` normalizes the GEX-style Edge payload exactly like `_edge_snapshot_payload` does today.
- `runtime_get(key: str) -> dict | None`, `runtime_set(key: str, value: dict) -> None`, and `runtime_delete(key: str) -> None` preserve the current repository-first runtime state behavior.
- `live_preview_key(preview_id: str) -> str`, `live_order_key(client_id: str) -> str`, `ccxt_preview_key(preview_id: str) -> str`, and `ccxt_order_key(exchange_id: str, client_id: str) -> str` return the same key strings currently returned by the private helpers.

- [ ] **Step 3: Replace `guardian_memory` and helper calls in `app.py`**

Inside `create_app`, replace the raw `guardian_memory` dict with:

```python
guardian_store = GuardianRuntimeStore(repository)
```

Update route bodies to call `guardian_store` methods. Keep route URLs and response shapes unchanged.

- [ ] **Step 4: Run Guardian tests**

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests\test_guardian_state.py tests\test_guardian_live_wiring.py tests\test_guardian_chart_ui.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```powershell
git add src\sentinel_chain\guardian\__init__.py src\sentinel_chain\guardian\state.py src\sentinel_chain\app.py tests\test_guardian_state.py
git commit -m "refactor: extract guardian runtime state"
```

---

## Task 6: Introduce Route Context And Move Guardian Routes

**Files:**
- Create: `src/sentinel_chain/api/context.py`
- Create: `src/sentinel_chain/guardian/api.py`
- Modify: `src/sentinel_chain/app.py`
- Test: `tests/test_guardian_live_wiring.py`, `tests/test_market_streaming.py`, `tests/test_ccxt_brokerage_wiring.py`

- [ ] **Step 1: Add route context dataclass**

Create `src/sentinel_chain/api/context.py`:

```python
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class RouteContext:
    engine: Any
    intake: Any
    repository: Any
    event_bus: Any
    runtime_controls: Any
    guardian_store: Any
    webhook_secret: str | None
    require_approval: bool
```

- [ ] **Step 2: Move Guardian route registration**

Create `src/sentinel_chain/guardian/api.py` with:

```python
from fastapi import FastAPI

from sentinel_chain.api.context import RouteContext


def register_guardian_api_routes(app: FastAPI, ctx: RouteContext) -> None:
    # Move the existing /guardian route decorators from create_app into this
    # function without changing URL paths, response payloads, or gate checks.
    # Nested route functions should close over ctx instead of create_app locals.
    return None
```

Move only these route groups from `create_app` first:

- `/guardian/drawings`
- `/guardian/edge/latest`
- `/guardian/edge/snapshot`
- `/guardian/ws/edge`
- `/guardian/ws/candles`
- `/guardian/live/status`
- `/guardian/live/preview`
- `/guardian/live/submit`

Keep the implementation behavior unchanged. The register function can define nested route functions just like `create_app` did, but the file boundary becomes smaller and testable.

- [ ] **Step 3: Call the registrar from `create_app`**

In `app.py`, after creating `RouteContext`, call:

```python
register_guardian_api_routes(app, route_context)
```

- [ ] **Step 4: Run focused tests**

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests\test_guardian_live_wiring.py tests\test_market_streaming.py tests\test_ccxt_brokerage_wiring.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```powershell
git add src\sentinel_chain\api\context.py src\sentinel_chain\guardian\api.py src\sentinel_chain\app.py
git commit -m "refactor: move guardian api routes"
```

---

## Task 7: Move Exchange, Bracket, Signal, And Backtest Routes

**Files:**
- Create: `src/sentinel_chain/exchanges/api.py`
- Create: `src/sentinel_chain/brackets/api.py`
- Create: `src/sentinel_chain/signals/api.py`
- Create: `src/sentinel_chain/backtests/__init__.py`
- Create: `src/sentinel_chain/backtests/api.py`
- Modify: `src/sentinel_chain/app.py`
- Test: existing focused suites

- [ ] **Step 1: Move exchange routes**

Move these route groups into `src/sentinel_chain/exchanges/api.py`:

- `/exchanges`
- `/exchanges/platforms`
- `/exchanges/ccxt/catalog`
- `/exchanges/{exchange_id}/ccxt/*`
- `/exchanges/{exchange_id}/capabilities`
- `/exchanges/{exchange_id}/adapter-status`
- `/exchanges/{exchange_id}/integration`
- `/exchanges/bitunix/futures/*`

Expose:

```python
def register_exchange_api_routes(app, ctx) -> None:
    # Move the existing exchange route decorators from create_app into this
    # function without changing URL paths, response payloads, or gate checks.
    return None
```

Run:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests\test_ccxt_brokerage_wiring.py tests\test_bitunix_adapter.py tests\test_exchange_capabilities.py tests\test_platform_registry.py -q
```

- [ ] **Step 2: Move bracket routes**

Move these route groups into `src/sentinel_chain/brackets/api.py`:

- `/brackets`
- `/brackets/risk-summary`
- `/brackets/health`
- `/brackets/coverage`
- `/brackets/oca-groups`
- `/brackets/{signal_id}/*`

Expose:

```python
def register_bracket_api_routes(app, ctx) -> None:
    # Move the existing bracket route decorators from create_app into this
    # function without changing URL paths, response payloads, or gate checks.
    return None
```

Run:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests\test_app.py tests\test_market_price_api.py tests\test_exit_triggers.py -q
```

- [ ] **Step 3: Move signal and approval routes**

Move these route groups into `src/sentinel_chain/signals/api.py`:

- `/approvals`
- `/approvals/{signal_id}/approve`
- `/approvals/{signal_id}/reject`
- `/signals`
- `/signals/parse-text`
- `/signals/preview-text`
- `/signals/submit-text`
- `/signals/submit`
- `/signals/preview`
- `/signals/preview-template`
- `/signals/preview-strategy`
- `/signals/submit-template`
- `/signals/exchange-plan`
- `/strategy-presets`
- `/strategy-presets/{preset_name}`
- `/bracket-templates`
- `/bracket-templates/{template_name}`

Run:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests\test_operator_ui.py tests\test_approvals.py tests\test_signals.py -q
```

- [ ] **Step 4: Move backtest routes**

Move these route groups into `src/sentinel_chain/backtests/api.py`:

- `/backtest/signal`
- `/backtest/bitunix-klines`
- `/backtest/batch`
- `/backtest/stress`

Expose:

```python
def register_backtest_api_routes(app, ctx) -> None:
    # Move the existing backtest route decorators from create_app into this
    # function without changing URL paths or response payloads.
    return None
```

Run:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests\test_backtest.py tests\test_app.py -q
```

- [ ] **Step 5: Remove addon monkey-patch wrappers from `app.py`**

After explicit route registration is inside `create_app`, remove the bottom sections:

- `# BEGIN SENTINEL CHAIN WAR ROOM ADDON ROUTES`
- `# BEGIN SENTINEL CHAIN GUARDIAN CHART ROUTES`

Replace with direct imports and calls in `create_app`:

```python
register_war_room_routes(app)
register_guardian_chart_routes(app)
```

- [ ] **Step 6: Run full suite and commit**

```powershell
& '.\.venv\Scripts\python.exe' -m pytest -q
git diff --check
git add src\sentinel_chain
git commit -m "refactor: split api route modules"
```

Expected: full suite passes and `app.py` is under 1000 lines.

---

## Task 8: Split Execution Domain

**Files:**
- Create: `src/sentinel_chain/execution_models.py`
- Create: `src/sentinel_chain/exit_orders.py`
- Create: `src/sentinel_chain/paper_exchange.py`
- Modify: `src/sentinel_chain/execution.py`
- Modify imports in modules and tests as needed
- Test: `tests/test_exit_triggers.py`, `tests/test_app.py`, `tests/test_backtest.py`

- [ ] **Step 1: Move dataclasses**

Move these classes unchanged into `src/sentinel_chain/execution_models.py`:

- `ExitOrder`
- `ExecutionCostConfig`
- `PaperLot`
- `PaperPosition`
- `PaperOrder`
- `ExecutionResult`

Keep re-exports in `execution.py`:

```python
from .execution_models import (
    ExecutionCostConfig,
    ExecutionResult,
    ExitOrder,
    PaperLot,
    PaperOrder,
    PaperPosition,
)
```

- [ ] **Step 2: Move exit order helpers**

Move these functions into `src/sentinel_chain/exit_orders.py`:

- `build_exit_orders`
- `_triggered_protective_exit`
- `_has_exit_plan`
- `_protective_stop_amendment`
- `_replace_or_append_stop`
- `_protective_trailing_amendment`
- `_replace_or_append_trailing_stop`
- `_take_profit_amendment`
- `_replace_take_profit`
- `_breakeven_exit_amendments`
- `_profit_lock_exit_amendments`
- `_protective_exit_price_amendments`
- `_profit_lock_price`
- `_sync_trailing_water_mark`
- `_has_trailing_distance`
- `_bracket_close_quantity`
- `_target_preview_lots`
- `_preview_lots_for_signal`
- `_nearest_protective_exit`
- `_lot_open_risk`
- `_trailing_starts_activated`
- `_has_trailing_activation`
- `_set_trailing_status`
- `_trailing_activation_price`
- `_trailing_distance`
- `_current_trailing_trigger`
- `_candidate_trailing_trigger`
- `_trailing_step_reached`
- `_trailing_step`
- `_filled_exit`
- `_allocated_entry_fee`
- `_proportional_fee`
- `_money`
- `_fixed8`
- `_order_fragment`
- `_paper_order_from_dict`
- `_exit_order_from_dict`
- `_bool_from_payload`

- [ ] **Step 3: Move `PaperExchange`**

Move `PaperExchange` into `src/sentinel_chain/paper_exchange.py`.

Keep compatibility import in `execution.py`:

```python
from .paper_exchange import PaperExchange
```

- [ ] **Step 4: Run execution tests**

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests\test_exit_triggers.py tests\test_app.py tests\test_backtest.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```powershell
git add src\sentinel_chain\execution.py src\sentinel_chain\execution_models.py src\sentinel_chain\exit_orders.py src\sentinel_chain\paper_exchange.py
git commit -m "refactor: split paper execution domain"
```

---

## Task 9: Split Auto-Charting Logic

**Files:**
- Create: `src/sentinel_chain/charting/candles.py`
- Create: `src/sentinel_chain/charting/indicators.py`
- Create: `src/sentinel_chain/charting/levels.py`
- Create: `src/sentinel_chain/charting/patterns.py`
- Create: `src/sentinel_chain/charting/trade_plans.py`
- Create: `src/sentinel_chain/charting/demo.py`
- Modify: `src/sentinel_chain/charting/automap.py`
- Test: `tests/test_war_room_automap.py`

- [ ] **Step 1: Move candle model and normalization**

Move to `charting/candles.py`:

- `NormalizedCandle`
- `_to_float`
- `_round`
- `_safe_div`
- `_percent_change`
- `_compact_symbol`
- `normalize_candles`
- `_series`

- [ ] **Step 2: Move indicators**

Move to `charting/indicators.py`:

- `sma`
- `ema`
- `true_range`
- `atr`
- `rsi`
- `macd`
- `bollinger`
- `vwap`
- `stochastic`
- `adx`
- `_last_number`
- `_last_n_numbers`
- `indicator_pack`

- [ ] **Step 3: Move levels and market structure**

Move to `charting/levels.py`:

- `adaptive_pivots`
- `cluster_support_resistance`
- `_line_from_points`
- `auto_trendlines`
- `volume_profile`
- `fibonacci_map`
- `imbalance_zones`
- `order_blocks`
- `market_structure`

- [ ] **Step 4: Move pattern detection**

Move to `charting/patterns.py`:

- `candle_patterns`
- `detect_divergences`
- `detect_chart_patterns`
- `signal_markers`

- [ ] **Step 5: Move trade planning and scoring**

Move to `charting/trade_plans.py`:

- `_nearest_level`
- `build_trade_plan`
- `confluence_score`
- `_build_why`
- `playbook_catalog`
- `risk_dashboard`

- [ ] **Step 6: Move demo and backtest helpers**

Move to `charting/demo.py`:

- `generate_demo_candles`
- `backtest_auto_strategy`

- [ ] **Step 7: Keep `automap.py` as orchestrator and re-export layer**

`automap.py` should keep:

- `analyze_market_structure`
- imports/re-exports for public functions currently used by `charting/routes.py` and tests.

- [ ] **Step 8: Run automap tests**

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests\test_war_room_automap.py -q
```

Expected: pass.

- [ ] **Step 9: Commit**

```powershell
git add src\sentinel_chain\charting tests\test_war_room_automap.py
git commit -m "refactor: split auto charting modules"
```

---

## Task 10: Split Guardian JavaScript

**Files:**
- Create: `src/sentinel_chain/static/sentinel_guardian_sample.js`
- Create: `src/sentinel_chain/static/sentinel_guardian_core.js`
- Create: `src/sentinel_chain/static/sentinel_guardian_chart.js`
- Create: `src/sentinel_chain/static/sentinel_guardian_panels.js`
- Create: `src/sentinel_chain/static/sentinel_guardian_trading.js`
- Create: `src/sentinel_chain/static/sentinel_guardian_streams.js`
- Modify: `src/sentinel_chain/static/sentinel_guardian.js`
- Modify: `src/sentinel_chain/static/sentinel_guardian.html`
- Modify: `src/sentinel_chain/sentinel_guardian_routes.py`
- Test: `tests/test_guardian_chart_ui.py`, `tests/test_guardian_static_contract.py`

- [ ] **Step 1: Extend allowed Guardian assets**

In `src/sentinel_chain/sentinel_guardian_routes.py`, add these assets to `_ALLOWED_ASSETS`:

```python
"sentinel_guardian_sample.js",
"sentinel_guardian_core.js",
"sentinel_guardian_chart.js",
"sentinel_guardian_panels.js",
"sentinel_guardian_trading.js",
"sentinel_guardian_streams.js",
```

- [ ] **Step 2: Move Edge sample data**

Move `EDGE_HEATMAP_SAMPLE` into `sentinel_guardian_sample.js`:

```javascript
window.SentinelGuardianSample = {
  edgeHeatmapSample: { /* existing EDGE_HEATMAP_SAMPLE object */ }
};
```

Replace the original declaration in `sentinel_guardian.js` with:

```javascript
const EDGE_HEATMAP_SAMPLE = window.SentinelGuardianSample.edgeHeatmapSample;
```

- [ ] **Step 3: Create a shared namespace**

At the top of `sentinel_guardian_core.js`, define:

```javascript
window.SentinelGuardian = window.SentinelGuardian || {};
```

Move DOM helpers, formatting helpers, `COLORS`, `state`, `api`, websocket URL helpers, local storage helpers, and `setStatus` into the namespace.

- [ ] **Step 4: Move chart functions**

Move candle generation, indicators, chart bounds, rendering, pointer handlers, drawing handlers, bracket calculation, and VCP detection into `sentinel_guardian_chart.js`.

Attach public functions to the namespace:

```javascript
Object.assign(window.SentinelGuardian, {
  loadDemo,
  loadVCP,
  loadEdge,
  renderChart,
  setTool,
  autoSafeBracket,
  applyInputsToBracket,
  signalFromGuardianPlan
});
```

- [ ] **Step 5: Move trading and backend action functions**

Move signal parsing, ticket building, paper preview/submit, live preview/submit, mark preview/apply, bracket actions, strategy actions, War Room actions, and exchange JSON loaders into `sentinel_guardian_trading.js`.

- [ ] **Step 6: Move panel rendering**

Move all `render*Panel`, `renderBackendPanels`, `renderGlobalStatus`, `renderDeskTable`, and table-rendering helpers into `sentinel_guardian_panels.js`.

- [ ] **Step 7: Move stream functions**

Move drawing persistence, Edge websocket, candle websocket, publish Edge sample, stop streams, and Bitunix candle load into `sentinel_guardian_streams.js`.

- [ ] **Step 8: Make `sentinel_guardian.js` the bootstrap only**

Leave only:

- `wireEvents`
- `init`
- keyboard shortcuts
- clock interval

- [ ] **Step 9: Update HTML script order**

In `sentinel_guardian.html`, load scripts in this order:

```html
<script src="static/sentinel_guardian_sample.js"></script>
<script src="static/sentinel_guardian_core.js"></script>
<script src="static/sentinel_guardian_chart.js"></script>
<script src="static/sentinel_guardian_panels.js"></script>
<script src="static/sentinel_guardian_trading.js"></script>
<script src="static/sentinel_guardian_streams.js"></script>
<script src="static/sentinel_guardian.js"></script>
```

- [ ] **Step 10: Run syntax checks**

```powershell
node --check src\sentinel_chain\static\sentinel_guardian_sample.js
node --check src\sentinel_chain\static\sentinel_guardian_core.js
node --check src\sentinel_chain\static\sentinel_guardian_chart.js
node --check src\sentinel_chain\static\sentinel_guardian_panels.js
node --check src\sentinel_chain\static\sentinel_guardian_trading.js
node --check src\sentinel_chain\static\sentinel_guardian_streams.js
node --check src\sentinel_chain\static\sentinel_guardian.js
```

Expected: all pass.

- [ ] **Step 11: Run Guardian tests**

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests\test_guardian_chart_ui.py tests\test_guardian_static_contract.py tests\test_guardian_live_wiring.py -q
```

Expected: pass.

- [ ] **Step 12: Run browser smoke**

Use the Playwright browser audit pattern from `work/ui_audit_guardian_result.json` or create `scripts/guardian_ui_smoke.py` if you want it committed. Minimum smoke:

```powershell
& '.\.venv\Scripts\python.exe' scripts\guardian_ui_smoke.py --url http://127.0.0.1:8004/guardian/ui
```

Expected: UI loads, 13 rail tabs switch, canvas nonblank, buy/sell paper previews work, live submit remains blocked.

- [ ] **Step 13: Commit**

```powershell
git add src\sentinel_chain\static\sentinel_guardian*.js src\sentinel_chain\static\sentinel_guardian.html src\sentinel_chain\sentinel_guardian_routes.py tests
git commit -m "refactor: split guardian ui scripts"
```

---

## Task 11: Split Legacy Operator JavaScript

**Files:**
- Create: `src/sentinel_chain/static/operator_state.js`
- Create: `src/sentinel_chain/static/operator_renderers.js`
- Create: `src/sentinel_chain/static/operator_trading.js`
- Create: `src/sentinel_chain/static/operator_charts.js`
- Modify: `src/sentinel_chain/static/app.js`
- Modify: `src/sentinel_chain/static/index.html`
- Test: `tests/test_operator_ui.py`

- [ ] **Step 1: Move operator state**

Move `appState`, state initialization, storage restore, and view activation into `operator_state.js`.

- [ ] **Step 2: Move renderers**

Move dashboard, orders, approvals, signals, exchange, strategy, audit, and table renderers into `operator_renderers.js`.

- [ ] **Step 3: Move trading actions**

Move signal submit, ticket preview/submit, close position, approval approve/reject, bracket amendments, market price update, exchange inspection, strategy copy/backtest, and audit export into `operator_trading.js`.

- [ ] **Step 4: Move chart drawing**

Move sparkline/backtest chart drawing and resize handling into `operator_charts.js`.

- [ ] **Step 5: Keep `app.js` as bootstrap**

Leave only dependency wiring:

```javascript
bindEvents();
applyStoredTicketDraft();
restoreAutoRefresh();
activateView(location.hash.slice(1) || "dashboard");
loadState();
```

- [ ] **Step 6: Run syntax and tests**

```powershell
node --check src\sentinel_chain\static\operator_state.js
node --check src\sentinel_chain\static\operator_renderers.js
node --check src\sentinel_chain\static\operator_trading.js
node --check src\sentinel_chain\static\operator_charts.js
node --check src\sentinel_chain\static\app.js
& '.\.venv\Scripts\python.exe' -m pytest tests\test_operator_ui.py -q
```

Expected: pass.

- [ ] **Step 7: Commit**

```powershell
git add src\sentinel_chain\static\operator_*.js src\sentinel_chain\static\app.js src\sentinel_chain\static\index.html tests\test_operator_ui.py
git commit -m "refactor: split operator ui scripts"
```

---

## Task 12: Final Cleanup And Enforcement

**Files:**
- Modify: `README.md`
- Modify: docs for Guardian/live wiring if route locations changed
- Create or modify: `tests/test_large_file_budget.py`

- [ ] **Step 1: Add a large-file budget test**

Create `tests/test_large_file_budget.py`:

```python
from pathlib import Path


MAX_LINES = {
    "src/sentinel_chain/app.py": 1000,
    "src/sentinel_chain/static/sentinel_guardian.js": 500,
    "src/sentinel_chain/static/app.js": 500,
    "src/sentinel_chain/execution.py": 250,
    "src/sentinel_chain/charting/automap.py": 450,
}


def test_refactored_large_files_stay_under_budget():
    root = Path(__file__).resolve().parents[1]
    offenders = {}
    for relative, limit in MAX_LINES.items():
        path = root / relative
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > limit:
            offenders[relative] = {"lines": line_count, "limit": limit}
    assert offenders == {}
```

- [ ] **Step 2: Update documentation**

Update:

- `README.md`
- `docs/SENTINEL_CHAIN_GUARDIAN_LIVE_WIRING.md`
- `docs/SENTINEL_CHAIN_GUARDIAN_BACKEND_WIRING.md`

Document the new module locations for Guardian routes, exchange routes, and UI script assets.

- [ ] **Step 3: Run full verification**

```powershell
& '.\.venv\Scripts\python.exe' -m pytest -q
node --check src\sentinel_chain\static\sentinel_guardian.js
node --check src\sentinel_chain\static\app.js
git diff --check
```

Expected: full suite passes, JS syntax checks pass, diff check has no whitespace errors.

- [ ] **Step 4: Commit**

```powershell
git add README.md docs tests\test_large_file_budget.py
git commit -m "test: enforce large file budgets"
```

---

## Known Issues To Fix During Or Before Refactor

These are not caused by the refactor, but they should be addressed before claiming the UI is feature-complete:

1. `src/sentinel_chain/static/sentinel_guardian.js` emits a positions table `data-close-symbol` button with no handler. Either wire it to inspect/load the position or remove the button.
2. Guardian War Room submit sends the War Room `signal` directly to `/signals/submit`, but `/war-room/ticket` currently emits `bracket.stop_loss` as a scalar. Normalize that ticket to top-level `stop_loss_price` and `take_profit_targets`, or make `signals.normalize_signal` accept scalar `bracket.stop_loss`.
3. Guardian exposes fewer bracket amendment controls than the legacy operator UI. Decide whether to add back amend stop, amend trailing stop, amend take profit, and close position actions before deleting legacy equivalents.
4. Bitunix public candle/ticker loading can return upstream 403/502 from this environment. Keep UI error handling visible and do not treat upstream denial as a local UI failure.

## Execution Order

Do not start with the JavaScript split. The safest order is:

1. Task 1
2. Task 2
3. Task 3
4. Task 4
5. Task 5
6. Task 6
7. Task 7
8. Task 8
9. Task 10
10. Task 11
11. Task 12

Task 9 can run in parallel with Task 7 only if a separate worker owns `src/sentinel_chain/charting/*` and does not touch `app.py`.

## Self-Review

- Spec coverage: The plan covers every current large hotspot over 1500 lines plus `styles.css` is intentionally deferred because CSS is lower behavioral risk than `app.py`, execution, charting, and trading UI code.
- Red-flag scan: No task uses forbidden filler phrases. Function move lists are explicit.
- Type consistency: Backend route extraction uses `RouteContext`; JS extraction uses a single `window.SentinelGuardian` namespace; compatibility imports preserve existing public names during extraction.
