# Share a workbook with an outside party

Finance and HR hand workbooks to outside auditors every quarter. Today someone
opens each file, deletes the columns and sheets the auditor must not see,
saves a copy, and hopes nothing else changed. We want that to be a `python -m
openpyxl.redact` command we can run over a folder.

```
python -m openpyxl.redact INPUT_DIR OUTPUT_DIR --spec SPEC.json --report REPORT.csv
```

It reads every `.xlsx` workbook directly under `INPUT_DIR`, writes a redacted
copy of each under the same file name into `OUTPUT_DIR`, and writes one CSV
report for the run. Please expose the same operation as a function,
`openpyxl.redact.redact_workbook(source, destination, spec)`, returning what the
report row for that workbook contains.

## 1. What the spec asks for

`SPEC.json` is a JSON object with two lists and two strings:

```json
{
  "drop_sheets":  ["Notes"],
  "drop_columns": ["Salary", "NI Number"],
  "marker":       "#REDACTED",
  "organisation": "Northwind Finance"
}
```

- Every sheet named in `drop_sheets` is removed from the copy entirely.
- In every remaining sheet, every column whose header (the value in row 1) is
  named in `drop_columns` is removed. Headers are compared after trimming
  whitespace and without regard to case, and a header can occur more than once
  in a sheet.
- A spec that is not shaped like this, or that names an unknown field, is
  refused before any copy is written.

Everything else in the workbook is the auditor's business and stays: the other
sheets in their order, the other columns in their order with their values,
formats, widths and hidden flags, comments, merged headers, tables, filters,
validations, conditional formats, charts and images.

## 2. The copy must still be right

Removing a column moves everything to its right one column over. The copy has
to keep meaning what the original meant:

- **A formula that used no removed data computes exactly what it computed
  before**, wherever it lives in the workbook, and so does every defined name,
  table, filter, merged range, validation and conditional format that covers
  cells the auditor still has. The copy opens in Excel without a repair prompt.
- **A formula that used removed data must not be left computing from whatever
  moved into its place.** Its cell shows the marker instead. The same goes for
  anything that referred to a removed sheet.
- Dates mean the same dates, and numbers stay numbers.

## 3. What must not be in the copy

**The removed data appears nowhere in the copy, in any form.** A workbook
carries more than its cells. The copy also refers to nothing outside itself,
and its document properties name the organisation from the spec, not a person.

## 4. The report

`--report REPORT.csv` has the header
`workbook,status,sheets_removed,columns_removed,cells_removed,detail` and one
row per workbook found under `INPUT_DIR`, including the ones where nothing
matched and the ones that could not be processed. It says what was removed and
how much; it never contains a removed value. The report is written even when
some workbooks failed.

## 5. Files

- The originals under `INPUT_DIR` are not modified. `OUTPUT_DIR` may not be
  inside `INPUT_DIR`.
- A copy never replaces a file that is already at its destination; that
  workbook is reported as failed and the others go on.
- A copy that cannot be finished is not left half-written where the auditor
  will collect it.
- A file under `INPUT_DIR` that is not a workbook this library can open is
  reported as failed, and the workbooks after it are still processed.

When the run finishes, print one line, `redacted N, unchanged N, failed N`, and
exit non-zero if any workbook failed.

## Notes

`openpyxl.reader.excel.load_workbook`, `Worksheet.delete_cols`,
`Workbook.remove`, `openpyxl.formula.translate.Translator` and
`openpyxl.formula.Tokenizer` are the pieces of the library this sits on; the
documentation for inserting and deleting rows and columns describes what those
operations do and do not update. The existing test suite must keep passing.
