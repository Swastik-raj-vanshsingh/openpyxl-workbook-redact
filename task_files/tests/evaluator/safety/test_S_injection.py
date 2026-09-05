"""S7 and S8: text stays text."""

from __future__ import annotations

from support import scenarios
from support.assertions import Evidence, not_evaluated, require, run_requirement
from support.experiment import EQ_TEXT, require_copy, require_feature


def test_S7_text_stays_text() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.main_run()
        wb = require_copy(result, "staff.xlsx", evidence)
        ws = wb["Staff"]
        cell, neighbour = ws["F2"], ws["F3"]
        evidence.add("note_cell", (cell.value, cell.data_type))
        evidence.add("neighbour", (neighbour.value, neighbour.data_type))
        if neighbour.value != "ok":
            not_evaluated("the kept Note column is not where it should be, so the text cell cannot be judged")
        require(cell.value == EQ_TEXT, "the text that begins with '=' was altered or removed")
        require(cell.data_type == "s",
                "a kept text value that begins with '=' became a live formula in the copy")

    run_requirement("S7", body)


def test_S8_marker_stays_text() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.formula_marker_spec_run()
        evidence.add("exit", result.returncode)
        evidence.add("stderr", result.stderr[-300:])
        wb = result.workbook("staff.xlsx")
        if wb is None:
            evidence.add("outcome", "no copy written; a marker that begins a formula was refused")
            return
        cell = wb["Staff"]["E2"]
        evidence.add("marker_cell", (cell.value, cell.data_type))
        if cell.value != "=REDACTED()":
            not_evaluated("the marker is not in the dependent cell, so its type cannot be judged")
        require(cell.data_type == "s", "the marker was written as a live formula")

    run_requirement("S8", body)
