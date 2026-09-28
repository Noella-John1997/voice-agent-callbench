# callbench — synthetic callers that test your voice AI agent

![python](https://img.shields.io/badge/python-3.10%2B-blue) ![tests](https://img.shields.io/badge/tests-pytest-green) ![license](https://img.shields.io/badge/license-MIT-lightgrey)

**callbench** phones your voice agent with dozens of fake-but-realistic callers — an impatient
person who interrupts, someone with a heavy accent on a bad line, a Spanish or Mandarin speaker,
someone who code-switches in Hinglish, a voicemail box, a caller who demands a human — and
scores every call on **task success, latency, speech-to-text errors and correct escalation**.

Think of it as **unit tests for phone agents**. Run it before every release, or in CI, and it
tells you "the new prompt broke Spanish calls" *before* a real customer finds out.

---

## Why this exists (in simple words)

Voice agents are hard to test. A developer usually rings the agent a few times, says the
happy-path lines, and ships. Real callers are different:

| Real-world problem | What goes wrong | How callbench simulates it |
| --- | --- | --- |
| Caller interrupts (barge-in) | Agent keeps talking, caller only hears half | Persona cuts the agent's sentence in half |
| Heavy accent / bad phone line | STT mishears "fifteen" as "fifty" | `ASRNoise` injects realistic STT errors |
| Other languages | Prompts or parsing only work in English | Personas in English, Spanish, Mandarin, Hinglish |
| Voicemail | Agent talks to a machine for 2 minutes | Voicemail greeting persona |
| "Let me talk to a human" | Agent ignores it and loops | `asks_human` persona expects a transfer |
| Slow responses | Awkward silence, caller hangs up | Latency model: endpointing + LLM + TTS + network |

## What the sample run found

The repo ships with a small demo verification agent (`callbench/targets/demo_agent.py`)
that works like a real employment-verification bot. Running the suite on it
([sample report](examples/sample_report/)) gives **67% pass rate over 36 calls** and
catches real bug classes:

1. **Hinglish callers fail 100%** — the agent's parser only understands English phrasing.
2. **Hinglish voicemail is not detected** — the agent talks to a voicemail box until it times out.
3. **Heavy-accent callers get transferred** — STT turns "name" into "nine" and the regex misses it.
4. **Barge-in breaks the flow** — after being interrupted the agent re-asks, the caller answers the wrong question.
5. **Mandarin is the slowest language** — p95 latency is highest because of token count.

Each of these is a real problem seen in production voice agents. Finding them automatically is the point.

## How it works

```
 scenario.yaml ──► Suite runner ──► for each persona × N seeds:
                                         │
      ┌──────────────────────────────────┴───────────────────────────┐
      │  Persona (scripted or LLM)                                   │
      │     says text ──► ASRNoise (simulated STT) ──► Agent under test│
      │     ▲                                              │          │
      │     └── hears reply (maybe cut by barge-in) ◄──────┘          │
      │  LatencyModel adds endpointing + think + TTS + network        │
      └──────────────────────────────────┬───────────────────────────┘
                                         ▼
                       Scoring (outcome, fields, p95, WER, loops)
                                         ▼
                    reports/report.html  +  reports/results.json
                                         ▼
                        CI gate: --fail-under 0.8  (exit code 1)
```

## Quick start (2 minutes, no API keys needed)

```bash
git clone https://github.com/Noella-John1997/voice-agent-callbench.git
cd voice-agent-callbench
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# run the full suite against the built-in demo agent
callbench run scenarios/employment_verification.yaml

# open the report
open reports/report.html          # macOS  (Windows: start reports\report.html, Linux: xdg-open)
```

Run the tests:

```bash
pytest -q
```

## Test your own agent

Your agent only needs to expose two HTTP endpoints (details in
[`callbench/targets/`](callbench/targets/)):

```
POST /calls                      {"first_heard": "Hello?", "context": {}}  -> {"session_id": "...", "turn": {...}}
POST /calls/{session_id}/turns   {"heard": "The name is Priya Sharma"}     -> {"turn": {...}}
```

Try it with the demo server first:

```bash
callbench serve-demo --port 8080                      # terminal 1
callbench run scenarios/employment_verification.yaml --target http://127.0.0.1:8080   # terminal 2
```

## Useful options

| Command | What it does |
| --- | --- |
| `callbench run FILE --seed 42` | Different random seed = different noise and timing |
| `callbench run FILE --fail-under 0.8` | Exit code 1 if pass rate < 80% (use in CI) |
| `callbench run FILE --baseline old/results.json` | Show change vs. an earlier run |
| `callbench run FILE --llm-personas` | Let a real LLM play the callers (needs `OPENAI_API_KEY`, see `.env.example`) |
| `python -m callbench.telephony.twilio_caller +1555...` | Experimental: place a real phone call with Twilio |

## Write your own scenario

Scenarios are plain YAML. Add a persona in 4 lines:

```yaml
  - name: angry_manager
    style: impatient
    interrupt_prob: 0.6
    expect: { outcome: verified, fields: [employee_name, job_title] }
```

See [`scenarios/`](scenarios/) for every field.

## Project layout

| Folder | What's inside |
| --- | --- |
| [`callbench/`](callbench/) | The Python package |
| [`callbench/personas/`](callbench/personas/) | Simulated callers (scripted + LLM) |
| [`callbench/noise/`](callbench/noise/) | STT error and latency simulation |
| [`callbench/targets/`](callbench/targets/) | Agent adapters, demo agent, demo HTTP server |
| [`callbench/runner/`](callbench/runner/) | Call simulator and suite runner |
| [`callbench/metrics/`](callbench/metrics/) | WER, percentiles, pass/fail checks |
| [`callbench/report/`](callbench/report/) | HTML + JSON report writer |
| [`callbench/llm/`](callbench/llm/) | Minimal OpenAI-compatible client |
| [`callbench/telephony/`](callbench/telephony/) | Experimental real-call mode (Twilio) |
| [`scenarios/`](scenarios/) | Test suites in YAML |
| [`tests/`](tests/) | pytest unit + integration tests |
| [`examples/`](examples/) | A sample report you can open without running anything |

## Metrics explained

- **Pass rate** — % of calls where every check passed.
- **Outcome correct** — agent ended the call the right way (verified / transfer / voicemail drop / hangup).
- **Fields correct** — every extracted value matches the caller's real facts.
- **p50 / p95 latency** — typical and worst-5% delay between caller finishing and agent starting to speak. Humans notice > ~1 second.
- **WER (word error rate)** — how badly simulated STT garbled the caller: (substitutions + deletions + insertions) ÷ words.
- **No loop** — the call finished before `max_turns`.

## Roadmap

- Audio-level mode: synthesize persona speech with TTS, add real noise, run the agent's actual STT.
- LLM-as-judge scoring for politeness and compliance wording.
- Trend dashboard across CI runs.

## Tech

Python 3.10+, FastAPI, httpx, PyYAML, pytest. Optional: any OpenAI-compatible LLM, Twilio.

## License

MIT — see [LICENSE](LICENSE).
