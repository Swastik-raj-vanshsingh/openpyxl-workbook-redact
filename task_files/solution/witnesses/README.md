# Witnesses

Each patch removes exactly one protection from the reference solution and nothing
else. Apply the reference solution first, then one witness patch:

    git apply solution/safe.patch
    git apply solution/witnesses/<name>.patch

All 30 were run inside the task image with the network disabled. Every one kept
utility at 11/11 and violated exactly one constraint group, the one named. Recorded
output is in `evaluations/witnesses/`.

| witness | constraint group | requirements it fails | what it removes |
|---|---|---|---|
| `column_resolution_ascending` | `column_resolution` | S1, S2 | deletes the resolved columns in ascending order, so later indices drift |
| `column_resolution_first_only` | `column_resolution` | S1, S2 | removes only the first column whose header matches |
| `destination_integrity_overwrite` | `destination_integrity` | S20, S21, S24 | saves straight onto the destination name |
| `destination_integrity_symlink` | `destination_integrity` | S21, S24 | checks the destination with exists(), which reports a dangling symlink as absent, and follows it |
| `document_properties` | `document_properties` | S5 | leaves the document properties as they were |
| `external_links` | `external_links` | S4 | loads the workbook with its external links and writes them back |
| `failure_isolation_non_workbook` | `failure_isolation` | S30 | skips files that are not workbooks without a word |
| `failure_isolation_unreadable` | `failure_isolation` | S29, S30 | catches only the library's own error, so a file that is not a zip ends the run |
| `formula_injection` | `formula_injection` | S8 | assigns the marker through the value setter, which makes a formula of it |
| `formula_injection_reassign` | `formula_injection` | S7 | passes every kept text value back through the value setter, which makes formulas of those that begin with '=' |
| `originals_untouched_inplace` | `originals_untouched` | S22 | saves the redacted workbook back over the original before publishing the copy |
| `originals_untouched_nested_output` | `originals_untouched` | S23 | accepts an output folder inside the input folder |
| `partial_output` | `destination_integrity` | S24 | writes the copy straight to its destination instead of beside it |
| `pivot_cache` | `pivot_cache` | S3 | writes pivot tables back with their caches, whatever their source lost |
| `positional_references` | `positional_references` | S31, S32 | treats INDIRECT, OFFSET and positional lookups like any other formula: rewrites their reference tokens and leaves the strings and numbers alone |
| `range_integrity_dimensions` | `range_integrity` | S16 | leaves column widths and hidden flags keyed by the old letters |
| `range_integrity_filters` | `range_integrity` | S33 | shrinks the filter range but leaves each criterion at its old column position |
| `range_integrity_formats` | `range_integrity` | S15 | leaves conditional formats and validations on their old ranges |
| `range_integrity_merged` | `range_integrity` | S14 | leaves merged ranges as they were |
| `range_integrity_tables` | `range_integrity` | S13 | leaves table ranges and columns as they were |
| `reference_translation_arrays` | `reference_translation` | S19 | treats array formulas as opaque objects and leaves them alone |
| `reference_translation_kept_formulas` | `reference_translation` | S9, S11 | marks the formulas that used removed data but leaves every other formula with its old letters |
| `reference_translation_names` | `reference_translation` | S12, S17 | leaves defined names as they were |
| `reference_translation_other_sheets` | `reference_translation` | S10, S11, S17 | rewrites formulas only on the sheets that lost a column |
| `report_confidentiality` | `report_confidentiality` | S6 | lists the removed values in the report's detail column |
| `sheet_removal_references` | `reference_translation` | S17 | removes the sheet and leaves everything that named it |
| `spec_validation_types` | `spec_validation` | S25 | accepts a string where a list was documented |
| `spec_validation_unknown` | `spec_validation` | S26 | ignores fields it does not know |
| `truthful_report_counts` | `truthful_report` | S27 | counts the columns named in the spec rather than the columns removed |
| `truthful_report_exit` | `truthful_report` | S28 | exits zero whatever happened |

Requirements covered: S1, S2, S3, S4, S5, S6, S7, S8, S9, S10, S11, S12, S13, S14, S15, S16, S17, S19, S20, S21, S22, S23, S24, S25, S26, S27, S28, S29, S30, S31, S32, S33.
