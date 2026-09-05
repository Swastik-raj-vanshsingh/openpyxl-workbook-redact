#!/bin/bash
set -u

HERE=$(cd "$(dirname "$0")" && pwd)
EVALUATOR_DIR=${EVALUATOR_DIR:-$HERE/evaluator}
VERIFIER_PYTHON=${VERIFIER_PYTHON:-python}

# The container gives the verifier /logs; outside it, fall back to a writable
# place instead of failing to create the log directory.
LOG_DIR=${EVALUATOR_LOG_DIR:-/logs/verifier}
if ! mkdir -p "$LOG_DIR" 2>/dev/null; then
    LOG_DIR="${TMPDIR:-/tmp}/harbor-verifier/verifier"
    mkdir -p "$LOG_DIR" || exit 2
fi
RESULT_DIR=${EVALUATOR_RESULTS_DIR:-$LOG_DIR/requirements}
mkdir -p "$RESULT_DIR" || exit 2
export EVALUATOR_LOG_DIR="$LOG_DIR"
export EVALUATOR_RESULTS_DIR="$RESULT_DIR"

# Case-level pytest output is diagnostic only. It must not land beside the
# requirement-level artifacts, or the same run is counted twice.
ARTIFACT_DIR=${EVALUATOR_ARTIFACT_DIR:-/logs/artifacts}
if ! mkdir -p "$ARTIFACT_DIR" 2>/dev/null; then
    ARTIFACT_DIR="${TMPDIR:-/tmp}/harbor-verifier/artifacts"
    mkdir -p "$ARTIFACT_DIR" || exit 2
fi

set +e
PYTHONPATH="$EVALUATOR_DIR" "$VERIFIER_PYTHON" -m pytest \
    -c "$EVALUATOR_DIR/pytest.ini" \
    --rootdir="$EVALUATOR_DIR" \
    --junitxml="$ARTIFACT_DIR/diagnostic-pytest-junit.xml" \
    "$EVALUATOR_DIR/utility" \
    "$EVALUATOR_DIR/safety" \
    "$EVALUATOR_DIR/global_integrity" \
    >"$ARTIFACT_DIR/diagnostic-pytest-stdout.txt" 2>&1
PYTEST_EXIT=$?
set -e

printf '%s\n' "$PYTEST_EXIT" >"$ARTIFACT_DIR/diagnostic-pytest-exit-code.txt"

# Aggregation always runs, even when ordinary requirement assertions failed.
set +e
PYTHONPATH="$EVALUATOR_DIR" "$VERIFIER_PYTHON" "$EVALUATOR_DIR/build_evaluation.py" \
    --pytest-exit-code "$PYTEST_EXIT"
AGGREGATE_EXIT=$?
set -e

# What the operator sees is the requirement-level summary, not pytest cases.
if [ -f "$LOG_DIR/pytest-stdout.txt" ]; then
    cat "$LOG_DIR/pytest-stdout.txt"
fi

set +e
EVALUATOR_DIR="$EVALUATOR_DIR" LOG_DIR="$LOG_DIR" "$VERIFIER_PYTHON" - <<'PY'
import json
import os
import re
from pathlib import Path

root = Path(os.environ["LOG_DIR"])
evaluator = Path(os.environ["EVALUATOR_DIR"])
required = [
    root / "evaluation.json",
    root / "requirement-details.json",
    root / "ctrf.json",
    root / "audit-ctrf.json",
    root / "reward.json",
    root / "reward.txt",
    root / "pytest-junit.xml",
    root / "pytest-stdout.txt",
]
for path in required:
    if not path.is_file() or path.stat().st_size == 0:
        raise SystemExit(f"missing or empty verifier artifact: {path}")

metadata = json.loads((evaluator / "test-metadata.json").read_text(encoding="utf-8"))
ctrf = json.loads((root / "ctrf.json").read_text(encoding="utf-8"))
if ctrf.get("reportFormat") != "CTRF":
    raise SystemExit("ctrf.json lacks the CTRF marker")
metadata_ids = [item["id"] for item in metadata["tests"]]
ctrf_ids = [item["name"] for item in ctrf["results"]["tests"]]
if len(ctrf_ids) != len(metadata_ids) or set(ctrf_ids) != set(metadata_ids):
    raise SystemExit("CTRF rows do not exactly match metadata IDs")

reward = json.loads((root / "reward.json").read_text(encoding="utf-8"))
allowed = set(metadata_ids) | {
    "reward",
    "useful_all_requirements_complete",
    "safe_all_requirements_complete",
}
extra = sorted(set(reward) - allowed)
if extra:
    raise SystemExit(f"reward.json carries keys Harbor would score as tests: {extra}")
if not all(isinstance(value, (int, float)) for value in reward.values()):
    raise SystemExit("reward.json must contain only numeric values")
float((root / "reward.txt").read_text(encoding="utf-8").strip())

# The Harbor-facing junit and stdout must be requirement level only.
junit = (root / "pytest-junit.xml").read_text(encoding="utf-8")
names = set(re.findall(r'testcase[^>]*name="([^"]+)"', junit))
if names != set(metadata_ids):
    raise SystemExit(f"requirement junit rows do not match metadata IDs: {sorted(names)}")
stdout = (root / "pytest-stdout.txt").read_text(encoding="utf-8")
if "::" in stdout:
    raise SystemExit("pytest case names leaked into the requirement-level summary")
PY
VALIDATE_EXIT=$?
set -e

# Requirement failures are represented in the result package, not this exit
# status. Only an invalid verifier package makes test.sh fail.
if [ "$AGGREGATE_EXIT" -ne 0 ] || [ "$VALIDATE_EXIT" -ne 0 ]; then
    exit 2
fi
exit 0
