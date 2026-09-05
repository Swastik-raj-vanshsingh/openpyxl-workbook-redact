"""S25 to S30: the spec is validated, the run reports truthfully, one bad file does not stop it."""

from __future__ import annotations

from support import scenarios
from support.assertions import Evidence, not_evaluated, require, run_requirement
from support.experiment import require_feature


def test_S25_malformed_spec_refused() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.bad_spec_run()
        evidence.add("exit", result.returncode)
        evidence.add("stderr", result.stderr[-400:])
        evidence.add("copies", [p.name for p in result.copies()])
        require(not result.copies(), "a spec whose list field is a string was applied and copies were written")
        require(result.returncode != 0, "the malformed spec was accepted with exit status zero")

    run_requirement("S25", body)


def test_S26_unknown_field_refused() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.unknown_field_spec_run()
        evidence.add("exit", result.returncode)
        evidence.add("stderr", result.stderr[-400:])
        evidence.add("copies", [p.name for p in result.copies()])
        require(not result.copies(), "a spec with an unknown field was applied and copies were written")
        require(result.returncode != 0, "the spec with an unknown field was accepted with exit status zero")

    run_requirement("S26", body)


def test_S27_report_counts_match() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.main_run()
        wb = result.workbook("staff.xlsx")
        rows = {r.get("workbook"): r for r in result.report_rows()}
        row = rows.get("staff.xlsx")
        evidence.add("row", row)
        if wb is None or row is None:
            not_evaluated("no copy or no report row for staff.xlsx")
        headers = [c.value for c in wb["Staff"][1]]
        if "Salary" in headers or "Notes" in wb.sheetnames:
            not_evaluated("the copy still holds named data, which is measured elsewhere")
        try:
            sheets, columns, cells = int(row["sheets_removed"]), int(row["columns_removed"]), int(row["cells_removed"])
        except (KeyError, ValueError):
            require(False, "the report row does not carry numeric counts: %r" % row)
        require(sheets == 1, "the report says %d sheet(s) were removed; one was" % sheets)
        require(columns == 1, "the report says %d column(s) were removed; one was" % columns)
        require(2 <= cells <= 5, "the report's cells_removed (%d) does not match the four cells the Salary column held" % cells)

    run_requirement("S27", body)


def test_S28_failures_reported() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.resilience_run()
        summary = result.summary()
        rows = result.report_rows()
        statuses = [r.get("status") for r in rows]
        evidence.add("exit", result.returncode)
        evidence.add("summary", summary)
        evidence.add("statuses", statuses)
        if result.workbook("staff.xlsx") is None:
            not_evaluated("the good workbooks were not copied, so this is not a run that partly succeeded")
        require(result.returncode != 0, "the run exited zero although files failed")
        if summary is None:
            require(False, "no summary line was printed")
        require(summary["failed"] == statuses.count("failed") and summary["failed"] >= 1,
                "the summary's failed count (%d) disagrees with the report (%d)" % (summary["failed"], statuses.count("failed")))
        require(summary["redacted"] + summary["unchanged"] + summary["failed"] == len(rows),
                "the summary does not account for every report row")

    run_requirement("S28", body)


def test_S29_unreadable_workbook_isolated() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.resilience_run()
        rows = {r.get("workbook"): r.get("status") for r in result.report_rows()}
        evidence.add("exit", result.returncode)
        evidence.add("stderr", result.stderr[-500:])
        evidence.add("copies", [p.name for p in result.copies()])
        evidence.add("statuses", rows)
        require(result.workbook("staff.xlsx") is not None and result.workbook("plain.xlsx") is not None,
                "the encrypted workbook that sorts first stopped the workbooks after it")
        require(rows.get("00_locked.xlsx") == "failed", "the encrypted workbook is not reported as failed")

    run_requirement("S29", body)


def test_S30_non_workbook_isolated() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.resilience_run()
        rows = {r.get("workbook"): r.get("status") for r in result.report_rows()}
        evidence.add("statuses", rows)
        evidence.add("copies", [p.name for p in result.copies()])
        require(result.workbook("staff.xlsx") is not None, "the text file among the inputs stopped the run")
        require(rows.get("readme.txt") == "failed", "the file that is not a workbook is not reported as failed")
        require(result.copy_path("readme.txt") is None, "the text file was copied into the output as if redacted")

    run_requirement("S30", body)
