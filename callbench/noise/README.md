# `noise/` — making the call realistically messy

## `asr_noise.py` — fake speech-to-text mistakes

Phone audio is 8 kHz and noisy, so STT engines mishear people. `ASRNoise(level)` copies common errors:

- **Sound-alike swaps**: "fifteen" → "fifty", "name" → "nine", "engineer" → "engine ear"
- **Dropped short words**: "the", "a", "to"
- **Mangled digits**: "2019" → "2090"

`level` goes from `0.0` (perfect) to `1.0` (terrible line). The persona's `accent_noise` setting controls it.

## `latency.py` — how long the caller waits

The delay a caller feels is:

```
endpointing (STT decides you stopped talking)
+ think time (the agent's LLM / logic)
+ TTS time-to-first-byte (voice starts)
+ network
```

`LatencyModel.sample()` draws each part with seeded randomness. Long or accented speech makes
endpointing slower, just like in real systems.
