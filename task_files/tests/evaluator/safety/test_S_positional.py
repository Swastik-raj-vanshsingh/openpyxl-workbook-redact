"""S31 and S32: a column named by text or by position."""

from __future__ import annotations

from support import scenarios
from support.assertions import Evidence, not_evaluated, require, run_requirement
from support.experiment import MARKER, formula_text, require_copy, require_feature


def _norm(text):
    return (text or "").replace(" ", "").replace("$", "").casefold()


def _marked(text):
    return text == MARKER or (text or "").startswith("#REF")


def test_S31_text_and_position_dependents_marked() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.main_run()
        ws = require_copy(result, "staff.xlsx", evidence)["Staff"]
        if ws["E2"].value != MARKER:
            not_evaluated("the directly referenced dependent formula is not marked, so this run does not mark "
                          "dependents at all; that is measured elsewhere")
        cells = {c: formula_text(ws[c]) for c in ("A8", "A10", "A12")}
        evidence.add("cells", cells)
        offending = {c: t for c, t in cells.items() if not _marked(t)}
        require(not offending,
                "formulas that named the removed Salary column by text or by position were left "
                "computing from whatever moved into column B: %r" % offending)

    run_requirement("S31", body)


def test_S32_text_and_position_kept_follow() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.main_run()
        ws = require_copy(result, "staff.xlsx", evidence)["Staff"]
        cells = {c: formula_text(ws[c]) for c in ("A9", "A11", "A13")}
        evidence.add("cells", cells)
        expected = {"A9": '=indirect("d2")', "A11": "=offset(a1,1,3)", "A13": '=vlookup("ann",a2:g3,4,false)'}
        offending = {c: t for c, t in cells.items()
                     if not _marked(t) and _norm(t) != expected[c]}
        require(not offending,
                "formulas that named the kept Manager column by text or by position now name a different "
                "column: %r" % offending)

    run_requirement("S32", body)
