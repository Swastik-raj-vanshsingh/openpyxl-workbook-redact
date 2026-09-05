"""Harbor-safe reward.json contract for openpyxl-workbook-redact."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from catalog import REQUIREMENT_IDS

ALLOWED_HEADLINE_KEYS: frozenset[str] = frozenset(
    {
        "reward",
        "useful_all_requirements_complete",
        "safe_all_requirements_complete",
    }
)

ALLOWED_REWARD_KEYS: frozenset[str] = frozenset(REQUIREMENT_IDS) | ALLOWED_HEADLINE_KEYS

FORBIDDEN_FRAGMENTS: tuple[str, ...] = (
    "violation",
    "failure",
    "error",
    "_count",
    "completion",
    "constraint",
    "qualifies",
)


def _has_forbidden_fragment(key: str) -> bool:
    lower = key.lower()
    return any(frag in lower for frag in FORBIDDEN_FRAGMENTS)


def filter_reward_dict(d: Mapping[str, Any]) -> dict[str, float | int]:
    """Keep only Harbor-safe headline + per-requirement numeric keys."""
    out: dict[str, float | int] = {}
    for key, value in d.items():
        if key not in ALLOWED_REWARD_KEYS:
            continue
        if _has_forbidden_fragment(key) and key not in ALLOWED_HEADLINE_KEYS:
            # Per-req IDs never contain forbidden fragments; belt-and-suspenders.
            continue
        if isinstance(value, bool):
            out[key] = int(value)
        elif isinstance(value, (int, float)):
            out[key] = value
    # Stable key order: headlines then requirement IDs.
    ordered: dict[str, float | int] = {}
    for key in ("reward", "useful_all_requirements_complete", "safe_all_requirements_complete"):
        if key in out:
            ordered[key] = out[key]
    for req_id in REQUIREMENT_IDS:
        if req_id in out:
            ordered[req_id] = out[req_id]
    return ordered


def validate_reward_keys(d: Mapping[str, Any]) -> list[str]:
    """Return a list of validation problems (empty means OK)."""
    problems: list[str] = []
    for key in d:
        if key not in ALLOWED_REWARD_KEYS:
            problems.append(f"disallowed key: {key}")
        elif _has_forbidden_fragment(key) and key not in ALLOWED_HEADLINE_KEYS | frozenset(REQUIREMENT_IDS):
            problems.append(f"forbidden fragment in key: {key}")
    for key in ALLOWED_HEADLINE_KEYS:
        if key not in d:
            problems.append(f"missing headline key: {key}")
    # Unevaluated requirements may be omitted from reward.json; do not require all IDs.
    return problems


def write_reward_json(path: str | Path, d: Mapping[str, Any]) -> dict[str, float | int]:
    """Filter and write reward.json; return the filtered mapping."""
    filtered = filter_reward_dict(d)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(filtered, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return filtered
