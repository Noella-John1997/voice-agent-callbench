"""Tiny LLM client. Works with any OpenAI-compatible /chat/completions API."""
from __future__ import annotations

import os
from typing import Protocol

import httpx


class ChatLLM(Protocol):
    def chat(self, messages: list[dict[str, str]]) -> str: ...


class OpenAICompatibleLLM:
    def __init__(self, api_key: str, base_url: str, model: str, timeout: float = 30.0):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def chat(self, messages: list[dict[str, str]]) -> str:
        resp = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "messages": messages, "temperature": 0.7, "max_tokens": 80},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


def llm_from_env() -> OpenAICompatibleLLM | None:
    """Return an LLM client if OPENAI_API_KEY is set, else None."""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    return OpenAICompatibleLLM(
        api_key=key,
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        model=os.getenv("CALLBENCH_LLM_MODEL", "gpt-4o-mini"),
    )
