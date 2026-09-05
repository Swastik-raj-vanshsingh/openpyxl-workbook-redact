"""S9 to S19: the copy keeps meaning what the original meant."""

from __future__ import annotations

from support import scenarios
from support.assertions import Evidence, not_evaluated, require, run_requirement
from support.experiment import MARKER, formula_text, refers_to, require_copy, require_feature


def _norm(text):
    return (text or "").replace(" ", "").replace("$", "").casefold()


def test_S9_same_sheet_references_shift() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.main_run()
        ws = require_copy(result, "staff.xlsx", evidence)["Staff"]
        ref, count = formula_text(ws["G2"]), formula_text(ws["G4"])
        evidence.add("G2", ref)
        evidence.add("G4", count)
        if not (ref or "").startswith("=") or not (count or "").startswith("="):
            not_evaluated("the kept formula cells are no longer formulas, so their references cannot be judged")
        require(_norm(ref) == "=d2", "the Ref formula still points at column E, which now holds Bonus: %r" % ref)
        require(_norm(count) == "=counta(d2:d3)",
                "the COUNTA formula still counts column E, which now holds Bonus: %r" % count)

    run_requirement("S9", body)


def test_S10_cross_sheet_dependent_marked() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.main_run()
        wb = require_copy(result, "staff.xlsx", evidence)
        if "Summary" not in wb.sheetnames:
            not_evaluated("the Summary sheet is missing from the copy")
        ws = wb["Summary"]
        a1, a4 = formula_text(ws["A1"]), formula_text(ws["A4"])
        evidence.add("A1", a1)
        evidence.add("A4", a4)
        offending = [t for t in (a1, a4) if t is not None and t != MARKER and not t.startswith("#REF")]
        require(not offending,
                "formulas on the Summary sheet that used the removed Salary column now read whatever "
                "moved into column B: %r" % offending)

    run_requirement("S10", body)


def test_S11_cross_sheet_reference_shifts() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.main_run()
        wb = require_copy(result, "staff.xlsx", evidence)
        if "Summary" not in wb.sheetnames:
            not_evaluated("the Summary sheet is missing from the copy")
        a2 = formula_text(wb["Summary"]["A2"])
        evidence.add("A2", a2)
        if not (a2 or "").startswith("="):
            not_evaluated("the cross-sheet formula is no longer a formula")
        require(_norm(a2) == "=staff!d2",
                "the Summary formula that referenced the kept Manager column still points at Staff!E2: %r" % a2)

    run_requirement("S11", body)


def test_S12_defined_names_follow() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.main_run()
        wb = require_copy(result, "staff.xlsx", evidence)
        names = {k: v.attr_text for k, v in wb.defined_names.items()}
        evidence.add("names", names)
        salary_name = names.get("SalaryRange")
        managers = names.get("Managers")
        summary_a6 = formula_text(wb["Summary"]["A6"]) if "Summary" in wb.sheetnames else None
        evidence.add("Summary_A6", summary_a6)
        if salary_name is not None:
            require(not refers_to(salary_name, "$B$", "B2", "B3") or (summary_a6 in (MARKER,) or (summary_a6 or "").startswith("#REF")),
                    "the SalaryRange name still covers column B, which now holds Dept, and formulas still use it: %r" % salary_name)
        require(managers is not None and _norm(managers) == "staff!d2:d3",
                "the Managers name still covers column E, which now holds Bonus: %r" % managers)

    run_requirement("S12", body)


def test_S13_table_shrinks() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.main_run()
        ws = require_copy(result, "staff.xlsx", evidence)["Staff"]
        tables = list(ws.tables.values())
        evidence.add("tables", [(t.name, t.ref, [c.name for c in t.tableColumns]) for t in tables])
        if not tables:
            evidence.add("outcome", "table dropped")
            return
        table = tables[0]
        columns = [c.name for c in table.tableColumns]
        require(table.ref.upper() == "A1:G3",
                "the table still spans A1:H3 although a column is gone; Excel will repair the file: %r" % table.ref)
        require("Salary" not in columns, "the table still declares the removed column: %r" % columns)

    run_requirement("S13", body)


def test_S14_merged_range_shrinks() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.main_run()
        ws = require_copy(result, "staff.xlsx", evidence)["Staff"]
        merged = sorted(str(m) for m in ws.merged_cells.ranges)
        evidence.add("merged", merged)
        if not merged:
            evidence.add("outcome", "unmerged")
            return
        require("A6:H6" not in merged,
                "the banner still merges A6:H6 although a column is gone: %r" % merged)
        require("A6:G6" in merged, "the merged banner no longer covers the kept columns: %r" % merged)

    run_requirement("S14", body)


def test_S15_formats_and_validations_follow() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.main_run()
        ws = require_copy(result, "staff.xlsx", evidence)["Staff"]
        cf_ranges = [str(cf.sqref) for cf in ws.conditional_formatting]
        dv_ranges = [str(dv.sqref) for dv in ws.data_validations.dataValidation]
        evidence.add("conditional_formatting", cf_ranges)
        evidence.add("data_validations", dv_ranges)
        require(not any("E2" in r for r in cf_ranges),
                "the conditional format that highlighted managers now highlights Bonus (column E): %r" % cf_ranges)
        if cf_ranges:
            require(any("D2" in r for r in cf_ranges),
                    "the conditional format no longer covers the Manager column: %r" % cf_ranges)
        require(not any("B2" in r for r in dv_ranges),
                "the validation that applied to Salary now applies to Dept (column B): %r" % dv_ranges)

    run_requirement("S15", body)


def test_S16_column_dimensions_follow() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.main_run()
        ws = require_copy(result, "staff.xlsx", evidence)["Staff"]
        dims = {k: (d.hidden, d.width) for k, d in ws.column_dimensions.items()}
        evidence.add("dimensions", dims)
        hidden = [k for k, (h, _) in dims.items() if h]
        require("D" in hidden, "the Manager column was hidden in the original and is visible in the copy: hidden=%r" % hidden)
        require("E" not in hidden and "B" not in hidden,
                "a column that was visible is now hidden: hidden=%r" % hidden)
        width_b = dims.get("B", (None, None))[1]
        require(width_b is not None and abs(width_b - 22.0) < 0.5,
                "the Dept column's width did not move with it: %r" % (dims.get("B"),))

    run_requirement("S16", body)


def test_S17_removed_sheet_unreferenced() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.main_run()
        wb = require_copy(result, "staff.xlsx", evidence)
        if "Notes" in wb.sheetnames:
            not_evaluated("the Notes sheet was not removed, so references to it are not at issue")
        names = {k: v.attr_text for k, v in wb.defined_names.items()}
        referring_names = [k for k, v in names.items() if refers_to(v, "Notes!")]
        referring_cells = []
        for ws in wb.worksheets:
            for row in ws.iter_rows():
                for cell in row:
                    text = formula_text(cell)
                    if cell.data_type == "f" and refers_to(text, "Notes!"):
                        referring_cells.append((ws.title, cell.coordinate, text))
        evidence.add("names_referring", referring_names)
        evidence.add("cells_referring", referring_cells)
        require(not referring_names, "defined names still point at the removed sheet: %r" % referring_names)
        require(not referring_cells, "formulas still point at the removed sheet: %r" % referring_cells)

    run_requirement("S17", body)


def test_S19_array_formula_follows() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.main_run()
        ws = require_copy(result, "staff.xlsx", evidence)["Staff"]
        cell = ws["H2"]
        text = formula_text(cell)
        ref = getattr(cell.value, "ref", None)
        evidence.add("H2", (type(cell.value).__name__, text, ref))
        if text == MARKER:
            evidence.add("outcome", "marked")
            return
        require(text is not None and _norm(text) == "=d2:d3",
                "the array formula over the kept Manager column was lost or still reads column E: %r" % text)
        if ref:
            require(ref.upper() == "H2:H3", "the array formula's range did not move with its cells: %r" % ref)

    run_requirement("S19", body)
