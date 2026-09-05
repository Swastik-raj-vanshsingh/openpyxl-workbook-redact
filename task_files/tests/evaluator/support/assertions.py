"""Requirement-aware assertions that preserve failure attribution."""

from __future__ import annotations

import json
import os
import tempfile
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


DEFAULT_LOG_DIR = "/logs/verifier"
DEFAULT_RESULT_DIR = "/logs/verifier/requirements"


def _writable(path: Path) -> Path:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError:
        path = Path(tempfile.gettempdir()) / "harbor-verifier" / path.name
        path.mkdir(parents=True, exist_ok=True)
    return path


def log_dir() -> Path:
    return _writable(Path(os.environ.get("EVALUATOR_LOG_DIR") or DEFAULT_LOG_DIR))


def results_dir() -> Path:
    configured = os.environ.get("EVALUATOR_RESULTS_DIR")
    if configured:
        return _writable(Path(configured))
    return _writable(log_dir() / "requirements")


class RequirementFailure(AssertionError):
    pass


class NotEvaluated(RuntimeError):
    def __init__(self, reason: str, *, deferred: bool = False) -> None:
        super().__init__(reason)
        self.deferred = deferred


@dataclass
class Evidence:
    items: list[dict[str, Any]] = field(default_factory=list)

    def add(self, label: str, value: Any) -> None:
        self.items.append({"label": label, "value": value})


def require(condition: bool, message: str, evidence: Any | None = None) -> None:
    if not condition:
        if evidence is not None:
            message = f"{message}; evidence={evidence!r}"
        raise RequirementFailure(message)


def not_evaluated(reason: str, *, deferred: bool = False) -> None:
    raise NotEvaluated(reason, deferred=deferred)


def _write_result(requirement_id: str, result: dict[str, Any]) -> None:
    result_dir = results_dir()
    destination = result_dir / f"{requirement_id}.json"
    temporary = result_dir / f".{requirement_id}.{os.getpid()}.tmp"
    temporary.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    temporary.replace(destination)


def run_requirement(requirement_id: str, body: Callable[[Evidence], None]) -> None:
    import pytest

    started = time.monotonic()
    evidence = Evidence()
    status = "passed"
    message = "requirement satisfied"
    error_trace = None
    deferred = False
    try:
        body(evidence)
    except NotEvaluated as exc:
        status = "not_evaluated"
        message = str(exc)
        deferred = bool(getattr(exc, "deferred", False))
    except RequirementFailure as exc:
        status = "failed"
        message = str(exc)
    except BaseException as exc:
        status = "error"
        message = f"{type(exc).__name__}: {exc}"
        error_trace = traceback.format_exc()

    duration_ms = max(1, round((time.monotonic() - started) * 1000))
    result = {
        "id": requirement_id,
        "status": status,
        "message": message,
        "duration_ms": duration_ms,
        "deferred": deferred,
        "evidence": evidence.items,
    }
    if error_trace is not None:
        result["traceback"] = error_trace
    _write_result(requirement_id, result)

    if status == "not_evaluated":
        pytest.skip(message)
    if status == "failed":
        pytest.fail(message, pytrace=False)
    if status == "error":
        raise RuntimeError(message)
