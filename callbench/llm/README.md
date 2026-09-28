# `llm/` — tiny LLM client

`providers.py` has one class, `OpenAICompatibleLLM`, that calls any `/chat/completions` API
(OpenAI, Azure OpenAI, Groq, a local vLLM or Ollama server…).

It's only used when you pass `--llm-personas`. Settings come from environment variables:

| Variable | Default |
| --- | --- |
| `OPENAI_API_KEY` | (required for LLM personas) |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` |
| `CALLBENCH_LLM_MODEL` | `gpt-4o-mini` |

Copy `.env.example` to `.env`, fill it in, and `export` the values (or use `direnv`).
