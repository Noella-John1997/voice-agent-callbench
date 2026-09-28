# `targets/` - the agent being tested

A **target** is anything that follows this 2-method contract (`base.py`):

```python
start(first_heard: str, context: dict) -> AgentTurn   # call just connected
respond(heard: str) -> AgentTurn                      # caller said something
```

`AgentTurn` holds the agent's reply text, an `action` (`continue`, `transfer`, `hangup`,
`voicemail_drop`), the fields it has extracted so far, and its think time in ms.

## Files

| File | What it is |
| --- | --- |
| `base.py` | The `Target` protocol |
| `demo_agent.py` | A reference employment-verification agent in 3 languages, with voicemail drop, KB answers and human transfer. **Deliberately imperfect** so callbench has bugs to find. |
| `http_target.py` | Tests any agent over HTTP (your real agent in any language/framework) |
| `demo_server.py` | FastAPI server that exposes the demo agent over the HTTP contract |

## HTTP contract (for your own agent)

```
POST /calls
  body:    {"first_heard": "Hello?", "context": {"seed": 1}}
  returns: {"session_id": "abc", "turn": {"text": "...", "action": "continue",
                                          "extracted": {}, "think_ms": 310.0, "language": "en"}}

POST /calls/{session_id}/turns
  body:    {"heard": "The employee's name is Priya Sharma."}
  returns: {"turn": {...same shape...}}
```

Tip: in a real Twilio + Deepgram agent, put this HTTP layer in front of the part that takes the
final transcript and decides what to say next. That's the "brain" callbench tests.
