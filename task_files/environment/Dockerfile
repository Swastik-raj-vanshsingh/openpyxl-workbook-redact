FROM python:3.11-slim-bookworm

ARG DEBIAN_FRONTEND=noninteractive
# openpyxl 3.1.5: canonical repository https://foss.heptapod.net/openpyxl/openpyxl,
# GitHub mirror https://github.com/quintagroup/openpyxl, tag 3.1.5 =
# commit 65a5b2aa1084862f8771346af1391a19fb903e9b. The source is vendored so the
# image builds without the network; the commit's tree hash is checked here and
# again by the verifier, so the starting point is exactly that commit's content.
ARG OPENPYXL_COMMIT=65a5b2aa1084862f8771346af1391a19fb903e9b
ARG OPENPYXL_TREE=c02c8b0f49329db2e41b70c90dc3b301e9d6863e

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY openpyxl-src.tar.gz /tmp/openpyxl-src.tar.gz

# The candidate checkout the agent works in.
RUN mkdir -p /workspace \
    && tar -xzf /tmp/openpyxl-src.tar.gz -C /workspace \
    && cd /workspace \
    && git init -q . \
    && git config user.email "tasks@example.invalid" \
    && git config user.name "Task Environment" \
    && git add -A \
    && git commit -qm "openpyxl at ${OPENPYXL_COMMIT}" \
    && test "$(git -C /workspace rev-parse HEAD^{tree})" = "${OPENPYXL_TREE}" \
    && printf '%s\n' "${OPENPYXL_COMMIT}" > /.harbor_base_commit \
    && printf '%s\n' "${OPENPYXL_TREE}" > /.harbor_base_tree

# An untouched copy of the released code, used by the verifier to prove the
# starting point does not already contain the graded behaviour.
RUN mkdir -p /opt/baseline/src \
    && tar -xzf /tmp/openpyxl-src.tar.gz -C /opt/baseline/src \
    && rm -f /tmp/openpyxl-src.tar.gz

RUN python -m pip install --no-cache-dir "pip>=25" "et_xmlfile" "lxml" "pytest==8.4.1" \
    && python -m pip install --no-cache-dir -e /workspace \
    && python -m venv /opt/baseline/venv \
    && /opt/baseline/venv/bin/python -m pip install --no-cache-dir "pip>=25" et_xmlfile \
    && /opt/baseline/venv/bin/python -m pip install --no-cache-dir /opt/baseline/src \
    && /opt/baseline/venv/bin/python -I -c "import openpyxl; print('baseline', openpyxl.__version__)"

RUN find /workspace /opt/baseline -name '__pycache__' -type d -prune -exec rm -rf {} + || true

WORKDIR /workspace

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CANDIDATE_REPO=/workspace \
    CANDIDATE_PYTHON=/usr/local/bin/python \
    BASELINE_PYTHON=/opt/baseline/venv/bin/python \
    BASELINE_SOURCE=/opt/baseline/src

CMD ["/bin/bash"]
