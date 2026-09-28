# `runner/` — running calls

## `simulator.py` → `simulate_call()`

Plays **one** call turn by turn:

1. Persona says its opening line ("Hello?" or a voicemail greeting).
2. The line goes through `ASRNoise` — the agent receives what STT "heard".
3. Agent replies; `LatencyModel` computes how long the caller waited.
4. Maybe a **barge-in**: the caller interrupts and only hears the first half of the reply.
5. Persona answers → back to step 2.
6. Stops when the agent transfers / hangs up / drops voicemail, the caller goes silent, or `max_turns` is hit.

It then decides the final **outcome** (`verified`, `transfer`, `voicemail_drop`, `hangup`,
`no_resolution`) and hands everything to `metrics.score_call()`.

## `suite.py` → `load_scenario()` and `run_suite()`

- `load_scenario()` reads a YAML file into personas + expectations.
- `run_suite()` calls every persona `runs_per_persona` times with different seeds, against the
  demo agent or an HTTP URL, and returns a list of `CallResult`.
