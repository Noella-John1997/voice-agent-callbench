# `report/` - output files

`writer.py` creates two files in the `--out` folder (default `reports/`):

- **`report.html`** - open in any browser. KPI tiles, pass rate by persona and language, and every call
  as an expandable transcript. Caller lines show **what STT heard** in orange when it differs from what
  was said, and agent lines show latency and barge-ins.
- **`results.json`** - the same data for scripts, dashboards or CI.

`compare_to_baseline()` diffs the headline numbers against an older `results.json`
(used by `--baseline`).
