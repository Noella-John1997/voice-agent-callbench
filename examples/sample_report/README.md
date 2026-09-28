# Sample report

Generated with:

```bash
callbench run scenarios/employment_verification.yaml --seed 7 --out examples/sample_report
```

| File | What it is |
| --- | --- |
| `report.html` | Human-readable report — open it in a browser |
| `results.json` | Full machine-readable results (every transcript, check and number) |

Headline: 36 calls, 67% pass rate. The failures (Hinglish, heavy accent, barge-in, Hinglish voicemail)
are the demo agent's real weaknesses — exactly what callbench is meant to find.
