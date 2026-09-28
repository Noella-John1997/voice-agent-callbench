# `tests/` — automated tests

Run everything with:

```bash
pytest -q
```

| File | What it checks |
| --- | --- |
| `test_metrics.py` | WER maths (substitution, insertion, deletion, Chinese) and percentiles |
| `test_noise.py` | STT noise is deterministic per seed; latency parts add up |
| `test_demo_agent.py` | Demo agent flows: happy path, voicemail, transfer, retries, KB answer, Spanish |
| `test_simulator.py` | Whole calls: cooperative passes, Hinglish voicemail is caught as a failure, latency gate works |
| `test_http_target.py` | The HTTP contract works end to end with the FastAPI demo server |
| `test_cli.py` | CLI writes reports, `--fail-under` returns exit code 1, `--baseline` diff works |
| `test_web.py` | Web API: page and static files load, personas listed, subset runs, limits enforced, live chat flow |
| `conftest.py` | Shared paths for tests |
