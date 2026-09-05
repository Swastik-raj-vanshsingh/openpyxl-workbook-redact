"""U1 to U11: the redaction command exists and does the documented job."""

from __future__ import annotations

import json
import subprocess

from support import scenarios
from support.assertions import Evidence, require, run_requirement
from support.experiment import (CANDIDATE_PYTHON, CANDIDATE_REPO, DEFAULT_SPEC, HIRE_DATE, MARKER,
                                Batch, run_python)

REPORT_HEADER = ["workbook", "status", "sheets_removed", "columns_removed", "cells_removed", "detail"]
KEPT_HEADERS = ["Name", "Dept", "Grade", "Manager", "Bonus", "Note", "Ref"]


def _module_present() -> bool:
    probe = run_python("import importlib.util as u; raise SystemExit(0 if u.find_spec('openpyxl.redact') else 3)")
    return probe.returncode == 0


def test_U1_command_registered() -> None:
    def body(evidence: Evidence) -> None:
        result = subprocess.run([CANDIDATE_PYTHON, "-m", "openpyxl.redact", "--help"], cwd=CANDIDATE_REPO,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
        text = (result.stdout + result.stderr).decode("utf-8", "replace")
        evidence.add("returncode", result.returncode)
        evidence.add("help", text[-800:])
        require(result.returncode == 0, "python -m openpyxl.redact --help did not succeed")
        require("--spec" in text and "--report" in text, "the help text does not document --spec and --report")

    run_requirement("U1", body)


def test_U2_copies_written() -> None:
    def body(evidence: Evidence) -> None:
        batch, result = scenarios.clean_run()
        evidence.add("returncode", result.returncode)
        evidence.add("stderr", result.stderr[-600:])
        evidence.add("copies", [p.name for p in result.copies()])
        require(result.returncode == 0, "the command failed on a folder with nothing wrong in it")
        for name in batch.workbook_names():
            require(result.workbook(name) is not None, "no readable copy of %s was written" % name)

    run_requirement("U2", body)


def test_U3_sheet_removed() -> None:
    def body(evidence: Evidence) -> None:
        batch, result = scenarios.main_run()
        wb = result.workbook("staff.xlsx")
        require(wb is not None, "no readable copy of staff.xlsx")
        evidence.add("sheets", wb.sheetnames)
        require("Notes" not in wb.sheetnames, "the sheet named in drop_sheets is still in the copy")
        require(wb.sheetnames == ["Staff", "Summary"], "the other sheets were dropped or reordered")

    run_requirement("U3", body)


def test_U4_columns_removed() -> None:
    def body(evidence: Evidence) -> None:
        batch, result = scenarios.main_run()
        wb = result.workbook("staff.xlsx")
        require(wb is not None, "no readable copy of staff.xlsx")
        ws = wb["Staff"]
        headers = [c.value for c in ws[1]]
        evidence.add("headers", headers)
        evidence.add("row2", [str(c.value) for c in ws[2]])
        require("Salary" not in headers, "the named column is still in the copy")
        require(headers[:7] == KEPT_HEADERS, "the kept columns are not in their original order: %r" % headers)
        require([ws["A2"].value, ws["B2"].value, ws["C2"].value, ws["D2"].value] == ["Ann", "Ops", "B", "Zed"],
                "kept values in row 2 moved or vanished")
        require([ws["A3"].value, ws["B3"].value, ws["C3"].value, ws["D3"].value] == ["Bob", "Eng", "C", "Yara"],
                "kept values in row 3 moved or vanished")

    run_requirement("U4", body)


def test_U5_direct_dependent_marked() -> None:
    def body(evidence: Evidence) -> None:
        batch, result = scenarios.main_run()
        wb = result.workbook("staff.xlsx")
        require(wb is not None, "no readable copy of staff.xlsx")
        ws = wb["Staff"]
        evidence.add("bonus_cells", [ws["E2"].value, ws["E3"].value])
        require(ws["E2"].value == MARKER and ws["E3"].value == MARKER,
                "the Bonus formula, which used the removed Salary cell, does not show the marker")

    run_requirement("U5", body)


def test_U6_report_written() -> None:
    def body(evidence: Evidence) -> None:
        batch, result = scenarios.main_run()
        header = result.report_header()
        rows = result.report_rows()
        evidence.add("header", header)
        evidence.add("rows", [(r.get("workbook"), r.get("status")) for r in rows])
        require(header == REPORT_HEADER, "the report header is not the documented one")
        names = {r.get("workbook") for r in rows}
        missing = [n for n in batch.workbook_names() if n not in names]
        require(not missing, "workbooks missing from the report: %r" % missing)

    run_requirement("U6", body)


def test_U7_summary_line() -> None:
    def body(evidence: Evidence) -> None:
        batch, result = scenarios.clean_run()
        summary = result.summary()
        evidence.add("stdout", result.stdout[-400:])
        evidence.add("summary", summary)
        require(summary is not None, "the documented summary line was not printed")
        require(summary == {"redacted": 1, "unchanged": 1, "failed": 0},
                "the summary counts do not match the run: %r" % summary)

    run_requirement("U7", body)


def test_U8_function_api() -> None:
    def body(evidence: Evidence) -> None:
        batch = Batch(staff=True, plain=False)
        try:
            destination = batch.output_dir / "staff.xlsx"
            batch.output_dir.mkdir()
            code = (
                "import json, sys; from openpyxl.redact import redact_workbook; "
                "row = redact_workbook(%r, %r, json.loads(%r)); print(json.dumps(dict(row)))"
                % (str(batch.files["staff"]), str(destination), json.dumps(DEFAULT_SPEC))
            )
            probe = run_python(code)
            out = probe.stdout.decode("utf-8", "replace")
            evidence.add("returncode", probe.returncode)
            evidence.add("stdout", out[-400:])
            evidence.add("stderr", probe.stderr.decode("utf-8", "replace")[-400:])
            require(probe.returncode == 0, "redact_workbook raised or is missing")
            require(destination.is_file(), "redact_workbook wrote no copy")
            row = json.loads(out.strip().splitlines()[-1])
            require(row.get("status") == "redacted", "the returned row does not say the workbook was redacted")
            require(set(REPORT_HEADER) <= set(row), "the returned row lacks report columns: %r" % sorted(row))
        finally:
            batch.close()

    run_requirement("U8", body)


def test_U9_comments_kept() -> None:
    def body(evidence: Evidence) -> None:
        batch, result = scenarios.main_run()
        wb = result.workbook("staff.xlsx")
        require(wb is not None, "no readable copy of staff.xlsx")
        ws = wb["Staff"]
        comments = {c.coordinate: c.comment.text for row in ws.iter_rows() for c in row if c.comment}
        evidence.add("comments", comments)
        require("D2" in comments, "the comment on the kept Manager cell did not survive")

    run_requirement("U9", body)


def test_U10_existing_tests_pass() -> None:
    def body(evidence: Evidence) -> None:
        present = _module_present()
        evidence.add("module_present", present)
        require(present, "openpyxl.redact is not present, so the released behaviour cannot be credited")
        result = subprocess.run(
            [CANDIDATE_PYTHON, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider",
             "openpyxl/worksheet/tests/test_worksheet.py", "openpyxl/workbook/tests", "openpyxl/formula/tests"],
            cwd=CANDIDATE_REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
        tail = result.stdout.decode("utf-8", "replace")[-600:]
        evidence.add("returncode", result.returncode)
        evidence.add("tail", tail)
        require(result.returncode == 0, "the library's existing tests no longer pass")

    run_requirement("U10", body)


def test_U11_unchanged_workbook_copied() -> None:
    def body(evidence: Evidence) -> None:
        batch, result = scenarios.main_run()
        wb = result.workbook("plain.xlsx")
        require(wb is not None, "no readable copy of plain.xlsx")
        ws = wb["Data"]
        evidence.add("values", [[c.value for c in row] for row in ws.iter_rows()])
        require(ws["A2"].value == "widgets" and ws["B2"].value == 3, "values of the unchanged workbook were altered")
        rows = {r.get("workbook"): r for r in result.report_rows()}
        evidence.add("row", rows.get("plain.xlsx"))
        require(rows.get("plain.xlsx", {}).get("status") == "unchanged",
                "the workbook where nothing matched is not reported as unchanged")

    run_requirement("U11", body)
