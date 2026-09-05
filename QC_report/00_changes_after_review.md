# Changes made because of the review passes

Three review passes were run against the finished package: the authoring
standard's QC prompt, the defect-first auditor prompt, and the thirteen quality
metrics. Everything they found had already been fixed by the witness sweep that
preceded them; this file records what the sweep found and what changed, so a
reader can see why the package has the shape it has. Every recorded run in
`evaluations/` is from after the last change.

## Found by the witness sweep

1. **Three mutations hit feature requirements instead of safety requirements.**
   Removing all formula rewriting failed U5, the obvious same-sheet dependent
   formula, rather than S9; rebuilding the copy in a fresh workbook failed U9
   because comments were lost, rather than the date requirement; over-counting
   removed columns made an untouched workbook report as redacted and failed U7
   and U11 rather than S27. Each witness was narrowed to the single decision its
   requirement measures: mark dependent formulas but leave kept ones with their
   old letters; over-count only when something was removed. The result is that
   S9 and S27 now have live, isolated witnesses.

2. **Two pairs of groups were one design decision each and were merged.** A
   witness that rewrites only the sheets that lost a column fails both the
   cross-sheet reference requirements (S10, S11) and the reference to a removed
   sheet (S17): `sheet_removal_references` is now part of
   `reference_translation`. A witness that saves straight onto the destination
   fails both the overwrite requirements (S20, S21) and the half-written copy
   (S24): `partial_output` is now part of `destination_integrity`. The package
   went from 16 groups to 14, then 13 (see item 3), and its independent-group
   counts are honest.

3. **One group was unreachable and was removed.** `date_system` (S18) assumed
   that a copy rebuilt in a fresh workbook would shift a 1904 date system's
   dates by four years. openpyxl converts dates to Python values on read and
   back on write with the workbook's own epoch, so a rebuilt copy keeps its
   dates, and the witness that flipped the epoch failed nothing. A requirement
   nothing can fail is noise; the group and its fixture were removed from the
   main run.

4. **Four requirements had no isolated witness.** S7 (kept text beginning with
   `=`), S9 (kept formulas shift), S22 (originals unchanged) and S27 (report
   counts) each gained one; all four fail exactly their own group.

## Found while building, before the sweep

5. **The feature workbook let a safety defect masquerade as a feature failure.**
   The first fixture removed two columns from the staff workbook the utility
   tests read. The naive composite, which deletes resolved indices in ascending
   order, removed the Manager column and kept the NI Number column there, so U4
   and U9 failed and all twelve of its safety failures were hidden behind a
   feature failure. The staff workbook now loses one column; the two-removal
   case and the duplicate header live in the payroll workbook, read only by S1
   and S2. The composite now scores 11 of 11 on utility and 12 of 13 groups on
   safety.

6. **Numeric leak tokens matched the theme.** A byte search for the removed
   salary `50000` found `<a:tint val="50000"/>` in the copy's theme part. The
   values are now distinctive (`50731`, `62842`, `71953`) and the search is
   restricted to the data-bearing parts of the file.

7. **The pivot fixture's owner values live in the cache definition, not the
   records part, and also in the pivot's rendered cells.** The probe scans the
   pivot-cache parts only, and the reference clears a removed pivot's rendered
   range as Excel does when a pivot table is deleted.

8. **A control-character round-trip does not fail openpyxl's save**, so the
   planned deterministic mid-save failure did not exist. S24 kills the process
   when the large copy first appears at its destination instead, and stands
   down with a reason when the kill misses its window.

9. **Evidence values that were not JSON-native crashed the requirement record.**
   An `ArrayFormula` object in U4's evidence made the whole requirement error.
   Evidence is now stringified when it is not JSON-native, and the one place it
   mattered was fixed at the source.

## Deliberately not changed

- **S24 stays timing-dependent.** No deterministic save-time failure exists in
  this library; the kill-on-appearance probe is honest about its window and
  records `not_evaluated` when it misses, never a verdict.
- **Comments and chart caches are not graded.** The ticket says comments stay,
  and openpyxl writes no chart caches, so neither is a reachable leak.

## Outstanding

Sealed calibration rollouts, three with the strongest Claude and three with the
strongest Codex, have not been run. Benchmark qualification is therefore
NOT_MEASURED. Everything establishable without agents is established and
recorded.
