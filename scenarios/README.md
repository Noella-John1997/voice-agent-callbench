# `scenarios/` — test suites

A scenario file lists the callers to simulate and what a good agent should do with each.

## Top-level fields

| Field | Meaning | Default |
| --- | --- | --- |
| `id` | Name used in reports | — |
| `description` | Free text | — |
| `runs_per_persona` | How many times to call each persona (different seeds) | 1 |
| `max_turns` | Stop a call after this many agent turns | 16 |
| `max_p95_latency_ms` | Latency budget for every call | 1200 |
| `default_facts` | Facts every persona knows unless overridden | — |

## Persona fields

| Field | Meaning |
| --- | --- |
| `name` | Label in the report |
| `language` | `en`, `es`, `zh`, `hinglish` |
| `style` | `cooperative`, `impatient`, `rambler`, `asks_human`, `kb_question`, `refuses`, `voicemail` |
| `facts` | Override `default_facts` |
| `accent_noise` | 0–1, how badly STT mishears this caller |
| `interrupt_prob` | 0–1, chance of barge-in on each agent turn |
| `kb_question` | Question asked by `kb_question` personas |
| `expect.outcome` | `verified`, `transfer`, `voicemail_drop`, `hangup` |
| `expect.fields` | Facts the agent must extract correctly |

`employment_verification.yaml` has 12 personas × 3 runs = 36 calls.
