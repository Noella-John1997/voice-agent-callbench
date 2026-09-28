# `metrics/` — scoring the calls

`scoring.py` contains:

| Function | What it does |
| --- | --- |
| `word_error_rate(ref, hyp)` | Standard WER using edit distance (dynamic programming). Chinese is scored per character. |
| `percentile(values, p)` | Nearest-rank percentile, used for p50 / p95 latency |
| `score_call(...)` | Runs the checks for one call and builds a `CallResult` |
| `summarize(results)` | Totals for the whole run: pass rate, by persona, by language, failed-check counts |

## Checks per call

- `outcome_correct` — did the call end the expected way?
- `fields_correct` — (verified calls only) do all extracted values match the facts? Compared case- and punctuation-insensitively.
- `latency_ok` — p95 latency within `max_p95_latency_ms`.
- `no_loop` — finished before `max_turns`.

A call **passes** only if all checks pass.
