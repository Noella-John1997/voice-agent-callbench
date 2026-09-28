# `web/` - the browser dashboard

`app.py` builds a FastAPI app (`create_app()`), started with `callbench web`.

| Endpoint | What it does |
| --- | --- |
| `GET /` | The dashboard page |
| `GET /api/scenario` | Personas in the scenario file |
| `POST /api/run` | Run the suite with your settings (personas, seed, runs, latency budget, extra noise/interruptions). Max 200 calls per run. |
| `POST /api/chat/start` | Start a live call with the demo agent (you are the caller) |
| `POST /api/chat/{id}` | Say something; returns what STT heard and the agent's reply |
| `GET /health` | Health check for hosting platforms |
| `GET /docs` | Interactive API docs (Swagger) |

Chat sessions are kept in memory for 30 minutes. The scenario file comes from `CALLBENCH_SCENARIO`
(default: `scenarios/employment_verification.yaml`).
