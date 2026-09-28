"""Small JSON store for scanner rules and hits.

This keeps the add-on dependency-free and works in local Windows checkouts. It is
safe to replace later with Sentinel Chain's database/event store.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional

from .scanner_models import ScanHit, ScannerRule, model_dump_compat


def default_store_path() -> Path:
    env = os.environ.get("SENTINEL_CHAIN_SCANNER_STORE")
    if env:
        return Path(env)
    root = os.environ.get("SENTINEL_CHAIN_HOME") or os.getcwd()
    return Path(root) / ".sentinel_chain" / "scanner_store.json"


class ScannerStore:
    def __init__(self, path: Optional[os.PathLike[str] | str] = None):
        self.path = Path(path) if path else default_store_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        if not self.path.exists():
            self._write({"rules": [], "hits": []})

    def _read(self) -> Dict[str, Any]:
        with self._lock:
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except FileNotFoundError:
                return {"rules": [], "hits": []}
            except json.JSONDecodeError:
                backup = self.path.with_suffix(self.path.suffix + ".corrupt")
                self.path.replace(backup)
                return {"rules": [], "hits": []}

    def _write(self, data: Dict[str, Any]) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp_name = tempfile.mkstemp(prefix="scanner_store_", suffix=".json", dir=str(self.path.parent))
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    json.dump(data, fh, indent=2, sort_keys=True)
                os.replace(tmp_name, self.path)
            finally:
                try:
                    if os.path.exists(tmp_name):
                        os.unlink(tmp_name)
                except Exception:
                    pass

    def list_rules(self, enabled_only: bool = False) -> List[ScannerRule]:
        data = self._read()
        rules = []
        for raw in data.get("rules", []):
            try:
                rule = ScannerRule(**raw)
            except Exception:
                continue
            if enabled_only and not rule.enabled:
                continue
            rules.append(rule)
        return rules

    def save_rule(self, rule: ScannerRule) -> ScannerRule:
        data = self._read()
        rules = data.setdefault("rules", [])
        as_dict = model_dump_compat(rule)
        for idx, existing in enumerate(rules):
            if existing.get("id") == rule.id:
                rules[idx] = as_dict
                break
        else:
            rules.append(as_dict)
        self._write(data)
        return rule

    def delete_rule(self, rule_id: str) -> bool:
        data = self._read()
        before = len(data.get("rules", []))
        data["rules"] = [r for r in data.get("rules", []) if r.get("id") != rule_id]
        changed = len(data["rules"]) != before
        if changed:
            self._write(data)
        return changed

    def add_hit(self, hit: ScanHit, max_hits: int = 1000) -> ScanHit:
        data = self._read()
        hits = data.setdefault("hits", [])
        hit_dict = model_dump_compat(hit)
        # Avoid duplicates if same run response is persisted twice.
        hits = [h for h in hits if h.get("id") != hit.id]
        hits.insert(0, hit_dict)
        data["hits"] = hits[:max_hits]
        self._write(data)
        return hit

    def list_hits(self, limit: int = 100, min_score: float = 0.0, symbol: Optional[str] = None) -> List[ScanHit]:
        data = self._read()
        result: List[ScanHit] = []
        symbol_norm = symbol.replace("/", "").upper() if symbol else None
        for raw in data.get("hits", []):
            try:
                hit = ScanHit(**raw)
            except Exception:
                continue
            if hit.score < min_score:
                continue
            if symbol_norm and hit.symbol.replace("/", "").upper() != symbol_norm:
                continue
            result.append(hit)
            if len(result) >= limit:
                break
        return result

    def get_hit(self, hit_id: str) -> Optional[ScanHit]:
        for hit in self.list_hits(limit=5000):
            if hit.id == hit_id:
                return hit
        return None

    def update_hit_status(self, hit_id: str, status: str) -> Optional[ScanHit]:
        data = self._read()
        updated = None
        for raw in data.get("hits", []):
            if raw.get("id") == hit_id:
                raw["status"] = status
                try:
                    updated = ScanHit(**raw)
                except Exception:
                    updated = None
                break
        if updated is not None:
            self._write(data)
        return updated
