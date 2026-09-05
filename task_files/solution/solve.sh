#!/bin/bash
# Apply the reference implementation of openpyxl.redact.
set -euo pipefail
REPO=${CANDIDATE_REPO:-/workspace}
HERE=$(cd "$(dirname "$0")" && pwd)
git -C "$REPO" apply --whitespace=nowarn "$HERE/safe.patch"
python -c "import openpyxl.redact; print('reference applied')"
