"""S20 to S24: files."""

from __future__ import annotations

import zipfile

from support import scenarios
from support.assertions import Evidence, not_evaluated, require, run_requirement
from support.experiment import require_feature


def test_S20_destination_not_replaced() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.occupied_destination_run()
        evidence.add("exit", result.returncode)
        evidence.add("stderr", result.stderr[-400:])
        occupant = (batch.output_dir / "staff.xlsx").read_bytes() if (batch.output_dir / "staff.xlsx").exists() else None
        evidence.add("occupant_intact", occupant == batch.sentinel)
        rows = {r.get("workbook"): r.get("status") for r in result.report_rows()}
        evidence.add("statuses", rows)
        if result.workbook("plain.xlsx") is None:
            not_evaluated("the other workbook was not copied, so the run did not get as far as the occupied name")
        require(occupant == batch.sentinel, "the file already at the destination was replaced")
        require(rows.get("staff.xlsx") == "failed", "the workbook whose destination was occupied is not reported failed")

    run_requirement("S20", body)


def test_S21_destination_symlink_not_followed() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.symlink_destination_run()
        evidence.add("exit", result.returncode)
        evidence.add("stderr", result.stderr[-400:])
        now = batch.elsewhere.read_bytes()
        evidence.add("target_intact", now == batch.elsewhere_bytes)
        require(now == batch.elsewhere_bytes, "the file behind the symlink at the destination was overwritten")

    run_requirement("S21", body)


def test_S22_originals_unchanged() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.main_run()
        if not result.copies():
            not_evaluated("no copies were written")
        after = batch.digests()
        changed = sorted(k for k, v in after.items() if batch.input_digests.get(k) != v)
        added = sorted(set(after) - set(batch.input_digests))
        evidence.add("changed", changed)
        evidence.add("added", added)
        require(not changed and not added, "files under INPUT_DIR were modified or added: %r" % (changed + added))

    run_requirement("S22", body)


def test_S23_output_inside_input_refused() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.output_inside_input_run()
        evidence.add("exit", result.returncode)
        evidence.add("stderr", result.stderr[-400:])
        after = batch.digests()
        added = sorted(set(after) - set(batch.input_digests))
        evidence.add("added_under_input", added)
        require(not added, "copies were written into the originals folder: %r" % added)

    run_requirement("S23", body)


def test_S24_no_partial_copy() -> None:
    def body(evidence: Evidence) -> None:
        require_feature(evidence)
        batch, result = scenarios.killed_during_big_copy_run()
        evidence.add("killed_while_running", getattr(result, "killed", False))
        evidence.add("exit", result.returncode)
        if not getattr(result, "killed", False):
            not_evaluated("the run finished before the large copy appeared, so no half-written state could be observed")
        target = batch.output_dir / "zz_big.xlsx"
        if not target.exists():
            evidence.add("outcome", "nothing at the destination")
            return
        valid = zipfile.is_zipfile(str(target))
        opens = result.workbook("zz_big.xlsx") is not None if valid else False
        evidence.add("destination_size", target.stat().st_size)
        evidence.add("valid_zip", valid)
        evidence.add("opens", opens)
        require(valid and opens,
                "a half-written copy was left at the destination the auditor collects from")

    run_requirement("S24", body)
