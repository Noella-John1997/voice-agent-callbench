# `callbench/` — the Python package

This folder is the installable package. `pip install -e .` makes the `callbench` command available.

| File / folder | Purpose |
| --- | --- |
| `cli.py` | The `callbench` command (`run`, `serve-demo`) |
| `__main__.py` | Lets you run `python -m callbench ...` |
| `types.py` | Shared dataclasses: `AgentTurn`, `TurnRecord`, `Expectation`, `CallResult`, `Action` |
| `personas/` | Fake callers |
| `noise/` | Simulated STT errors and latency |
| `targets/` | The agent being tested (demo agent, HTTP adapter) |
| `runner/` | Runs calls and suites |
| `metrics/` | Turns transcripts into scores |
| `report/` | Writes HTML and JSON reports |
| `llm/` | Small LLM client for LLM-played personas |
| `telephony/` | Experimental real phone calls |

**Data flow in one line:** `runner` asks a `persona` to speak → `noise` garbles it → `targets` agent replies →
`metrics` scores the call → `report` writes the files.
