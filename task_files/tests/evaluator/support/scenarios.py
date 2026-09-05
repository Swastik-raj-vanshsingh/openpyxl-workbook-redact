"""The runs every requirement observes, each built once and shared.

Hostile situations live in their own runs where a defect in handling one could
otherwise make an unrelated requirement fail.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable

from support.experiment import DEFAULT_SPEC, Batch, Result, run_redact, run_redact_and_kill

_CACHE: dict[str, tuple[Batch, Result]] = {}
_KEEP: list[Batch] = []


def _cached(name: str, build: Callable[[], tuple[Batch, Result]]) -> tuple[Batch, Result]:
    if name not in _CACHE:
        batch, result = build()
        _KEEP.append(batch)
        _CACHE[name] = (batch, result)
    return _CACHE[name]


def main_run() -> tuple[Batch, Result]:
    """The staff workbook, a plain one, the repository's pivot and link fixtures."""

    def build() -> tuple[Batch, Result]:
        batch = Batch(staff=True, plain=True, pivot=True, links=True)
        return batch, run_redact(batch)

    return _cached("main", build)


def clean_run() -> tuple[Batch, Result]:
    """Only well-formed workbooks with something to redact, so the exit status is unclouded."""

    def build() -> tuple[Batch, Result]:
        batch = Batch(staff=True, plain=True)
        return batch, run_redact(batch)

    return _cached("clean", build)


def duplicate_header_run() -> tuple[Batch, Result]:
    """Two removals far apart and the same header twice, once spelt loosely."""

    def build() -> tuple[Batch, Result]:
        batch = Batch(staff=False, plain=False, dup=True)
        return batch, run_redact(batch)

    return _cached("dup", build)


def resilience_run() -> tuple[Batch, Result]:
    """An encrypted workbook that sorts first and a text file, beside good workbooks."""

    def build() -> tuple[Batch, Result]:
        batch = Batch(staff=True, plain=True, locked=True, non_workbook=True)
        return batch, run_redact(batch)

    return _cached("resilience", build)


def occupied_destination_run() -> tuple[Batch, Result]:
    """A file is already where one copy would go."""

    SENTINEL = b"operator's own file; do not replace\n"

    def build() -> tuple[Batch, Result]:
        batch = Batch(staff=True, plain=True)
        batch.output_dir.mkdir()
        (batch.output_dir / "staff.xlsx").write_bytes(SENTINEL)
        batch.sentinel = SENTINEL  # type: ignore[attr-defined]
        return batch, run_redact(batch)

    return _cached("occupied", build)


def symlink_destination_run() -> tuple[Batch, Result]:
    """The destination name is a symlink to a file elsewhere."""

    def build() -> tuple[Batch, Result]:
        batch = Batch(staff=False, plain=True)
        batch.output_dir.mkdir()
        elsewhere = batch.root / "elsewhere.bin"
        elsewhere.write_bytes(b"quarterly close, do not touch\n")
        os.symlink(str(elsewhere), str(batch.output_dir / "plain.xlsx"))
        batch.elsewhere = elsewhere  # type: ignore[attr-defined]
        batch.elsewhere_bytes = elsewhere.read_bytes()  # type: ignore[attr-defined]
        return batch, run_redact(batch)

    return _cached("symlink", build)


def output_inside_input_run() -> tuple[Batch, Result]:
    def build() -> tuple[Batch, Result]:
        batch = Batch(staff=True, plain=False)
        return batch, run_redact(batch, output_dir=batch.input_dir / "out")

    return _cached("inside", build)


def bad_spec_run() -> tuple[Batch, Result]:
    """drop_columns given as a string, not a list."""

    def build() -> tuple[Batch, Result]:
        batch = Batch(staff=True, plain=False)
        bad = dict(DEFAULT_SPEC); bad["drop_columns"] = "Salary"
        return batch, run_redact(batch, spec_path=batch.write_spec(bad))

    return _cached("bad_spec", build)


def unknown_field_spec_run() -> tuple[Batch, Result]:
    def build() -> tuple[Batch, Result]:
        batch = Batch(staff=True, plain=False)
        bad = dict(DEFAULT_SPEC); bad["drop_rows"] = ["1"]
        return batch, run_redact(batch, spec_path=batch.write_spec(bad))

    return _cached("unknown_field", build)


def formula_marker_spec_run() -> tuple[Batch, Result]:
    """A marker the operator typed that happens to begin a formula."""

    def build() -> tuple[Batch, Result]:
        batch = Batch(staff=True, plain=False)
        spec = dict(DEFAULT_SPEC); spec["marker"] = "=REDACTED()"
        return batch, run_redact(batch, spec_path=batch.write_spec(spec))

    return _cached("formula_marker", build)


def killed_during_big_copy_run() -> tuple[Batch, Result]:
    """The process is killed the moment the large copy appears at its destination."""

    def build() -> tuple[Batch, Result]:
        batch = Batch(staff=False, plain=True, big=True)
        return batch, run_redact_and_kill(batch, "zz_big.xlsx")

    return _cached("killed", build)
