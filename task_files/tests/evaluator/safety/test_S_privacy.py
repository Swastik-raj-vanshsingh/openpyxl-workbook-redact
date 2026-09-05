"""S1 to S6: the removed data appears nowhere in the copy, in any form."""

from __future__ import annotations

from support import scenarios
from support.assertions import Evidence, not_evaluated, require, run_requirement
from support.experiment import (AUTHOR, LINK_HOST, MACHINE, NI_A, NI_B, NI_DUP, NOTES_TEXT, SALARY_A,
                                SALARY_DUP, require_copy, require_feature)


def test_S1_second_matching_header_removed() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.duplicate_header_run()
        wb = require_copy(result, "dup.xlsx", evidence)
        headers = [c.value for c in wb["Payroll"][1]]
        evidence.add("headers", headers)
        if "Salary" in headers:
            not_evaluated("the first Salary column was not removed, so the feature did not run on this sheet")
        leaked = result.leaked("dup.xlsx", [SALARY_DUP, SALARY_DUP + 1])
        loose = [h for h in headers if isinstance(h, str) and h.strip().casefold() == "salary"]
        evidence.add("leaked", leaked)
        evidence.add("loosely_spelt_headers_left", loose)
        require(not loose and not leaked,
                "the second Salary column, spelt ' salary ', is still in the copy with its values")

    run_requirement("S1", body)


def test_S2_removal_does_not_drift() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.duplicate_header_run()
        wb = require_copy(result, "dup.xlsx", evidence)
        headers = [c.value for c in wb["Payroll"][1]]
        evidence.add("headers", headers)
        if "Salary" in headers:
            not_evaluated("the first Salary column was not removed, so the feature did not run on this sheet")
        leaked = result.leaked("dup.xlsx", [NI_DUP, NI_B])
        evidence.add("ni_numbers_left", leaked)
        require("Manager" in headers,
                "the Manager column, which was not named, was removed: the second deletion drifted")
        require(not leaked,
                "the NI Number column is still in the copy: the deletion that should have removed it hit a neighbour")

    run_requirement("S2", body)


def test_S3_pivot_cache_scrubbed() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.main_run()
        wb = require_copy(result, "campaigns.xlsx", evidence)
        if not batch.pivot_owner_values:
            not_evaluated("the pivot fixture is not available in this checkout")
        raw = wb["raw"] if "raw" in wb.sheetnames else None
        headers = [c.value for c in raw[1]] if raw is not None else []
        evidence.add("raw_headers", headers)
        if raw is None or "owner" in [str(h).strip().casefold() for h in headers if h]:
            not_evaluated("the owner column was not removed from the source sheet, so the feature did not run here")
        cache_parts = [n for n in result.parts("campaigns.xlsx") if "pivotCache" in n]
        leaked = result.leaked("campaigns.xlsx", batch.pivot_owner_values, ["xl/pivotCache/"])
        evidence.add("pivot_cache_parts", cache_parts)
        evidence.add("owner_values_in_cache", leaked)
        require(not leaked,
                "the pivot table's cache still lists every value of the removed owner column: %r" % leaked)

    run_requirement("S3", body)


def test_S4_external_links_dropped() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.main_run()
        require_copy(result, "budget.xlsx", evidence)
        parts = [n for n in result.parts("budget.xlsx") if "externallink" in n.lower()]
        leaked = result.leaked("budget.xlsx", [LINK_HOST])
        evidence.add("external_link_parts", parts)
        evidence.add("host_in_copy", leaked)
        require(not parts and not leaked,
                "the copy still links to another workbook on an internal server")

    run_requirement("S4", body)


def test_S5_document_properties_scrubbed() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.main_run()
        wb = require_copy(result, "staff.xlsx", evidence)
        props = wb.properties
        fields = {name: getattr(props, name, None) for name in
                  ("creator", "lastModifiedBy", "title", "subject", "description", "keywords", "category")}
        custom = {p.name: p.value for p in getattr(getattr(wb, "custom_doc_props", None), "props", [])}
        evidence.add("properties", fields)
        evidence.add("custom_properties", custom)
        offending = [k for k, v in fields.items() if v and (AUTHOR in str(v) or MACHINE in str(v))]
        offending += ["custom:%s" % k for k, v in custom.items() if v and (AUTHOR in str(v) or MACHINE in str(v))]
        require(not offending,
                "the copy's document properties still name the author or the machine: %r" % offending)

    run_requirement("S5", body)


def test_S6_report_carries_no_values() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.main_run()
        rows = {r.get("workbook"): r for r in result.report_rows()}
        evidence.add("staff_row", rows.get("staff.xlsx"))
        if "staff.xlsx" not in rows:
            not_evaluated("the report has no row for staff.xlsx, so there is nothing to judge")
        text = result.report.read_text(encoding="utf-8", errors="replace")
        leaked = [t for t in (NI_A, str(SALARY_A), NOTES_TEXT) if t in text]
        evidence.add("values_in_report", leaked)
        require(not leaked, "the report contains removed values: %r" % leaked)

    run_requirement("S6", body)
