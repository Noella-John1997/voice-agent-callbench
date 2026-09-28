# `personas/` — the simulated callers

A **persona** is a fake caller with three things:

1. **Facts** — the truth they know (employee name, dates, job title).
2. **Language** — `en`, `es`, `zh` or `hinglish`.
3. **Style** — how they behave on the phone.

| Style | Behaviour | A good agent should… |
| --- | --- | --- |
| `cooperative` | Answers every question | verify the employee |
| `impatient` | Adds "just get to the point", interrupts (`interrupt_prob`) | still verify |
| `rambler` | Adds filler before each answer | still extract the right values |
| `asks_human` | Asks for a real person immediately | transfer |
| `kb_question` | Asks "what company is this?" first | answer, then continue |
| `refuses` | Won't share anything | end politely |
| `voicemail` | Is a voicemail greeting | leave a message and hang up |

## Files

- `base.py` — `PersonaSpec` (settings loaded from YAML) and the `Persona` interface (`opening()`, `reply()`).
- `scripted.py` — `ScriptedPersona`: rule-based and deterministic. It spots what the agent asked
  (name? dates? title? "is that correct?") using regex patterns in 4 languages and answers from its facts.
  Same seed → same call, which makes regressions easy to see.
- `llm_persona.py` — `LLMPersona`: an LLM plays the caller for more natural, unpredictable conversations.
  Enable with `--llm-personas`.

## Add a new language

Add a new key to `PHRASES` in `scripted.py` with the same phrase keys (`hello`, `yes`, `name`, …),
and add the question words to `ASK_PATTERNS`.
