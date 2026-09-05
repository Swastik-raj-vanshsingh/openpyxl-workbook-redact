# Independent agent run: Claude Opus, ticket only

An independent Claude Opus agent was given `instruction.md` and a clean checkout of the
pinned openpyxl tree, with no access to the tests, the manifest, the reference or the
witness patches, and asked to do the ticket. It wrote `openpyxl/redact.py` (kept here,
unedited, as `submission/redact.py`, 1499 lines). The agent's session was cut off by a usage
limit while it was running its own smoke test; the module it had written was complete and
was graded as it stood, inside the task image with the network disabled, by the verifier in
`task_files/tests`. The verifier's own artifacts are in this directory.

| utility | groups violated | families | reward |
|---|---|---|---|
| 11/11 | 2 (failure_isolation, positional_references) | 2 | 0.0 |

## What it defended

Header resolution by exact match with duplicates refused, descending deletes, a tokenizer
pass over every sheet's formulas with the marker for dependents, defined names, tables and
their columns, merged ranges, conditional formats, validations, column dimensions, freeze
panes, print areas, hyperlinks, filter criteria, the pivot cache of a removed sheet, external
links, every document property, the report's detail column, exit status, a temp file and
rename at the destination, and the spec's types and fields.

## What it missed

- **S30** (`failure_isolation`): the file that is not a workbook is not reported as failed
- **S31** (`positional_references`): formulas that named the removed Salary column by text or by position were left computing from whatever moved into column B: {'A8': '=INDIRECT("B2")', 'A10': '=OFFSET(A1,1,1)'}
- **S32** (`positional_references`): formulas that named the kept Manager column by text or by position now name a different column: {'A9': '=INDIRECT("E2")', 'A11': '=OFFSET(A1,1,4)'}

The first is a formula whose dependence on the removed column is written as a string
(`=INDIRECT("B2")`) or as a position (`=OFFSET(A1,1,1)`): the agent's rewrite handles every
reference token and leaves text and numbers alone, so in its copy those cells compute from
the department that moved into column B. It marked positional lookups over ranges that lost a
column (`VLOOKUP(...,2,...)`), so only the text-addressed forms failed. The second is the
report status for a file that is not a workbook.

Requirements recorded as `not_evaluated` in this run: none.
