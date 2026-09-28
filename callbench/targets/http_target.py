"""Test ANY agent that speaks this tiny HTTP contract:

    POST {base}/calls                    body {"first_heard": str, "context": {...}}
         -> {"session_id": str, "turn": AgentTurnJSON}
    POST {base}/calls/{session_id}/turns body {"heard": str}
         -> {"turn": AgentTurnJSON}

AgentTurnJSON = {"text": str, "action": "continue|transfer|hangup|voicemail_drop",
                 "extracted": {...}, "think_ms": float, "language": str}

`callbench serve-demo` starts a server with exactly this contract so you can
see a working example.
"""
from __future__ import annotations

import time

import httpx

from ..types import Action, AgentTurn


def _to_turn(d: dict, measured_ms: float) -> AgentTurn:
    return AgentTurn(
        text=d["text"],
        action=Action(d.get("action", "continue")),
        extracted=d.get("extracted", {}),
        # If the server doesn't report think time, use the measured round trip.
        think_ms=float(d.get("think_ms") or measured_ms),
        language=d.get("language", "en"),
    )


class HTTPTarget:
    def __init__(self, base_url: str, timeout: float = 15.0, client: httpx.Client | None = None):
        self.base = base_url.rstrip("/")
        self.client = client or httpx.Client(timeout=timeout)
        self.session_id: str | None = None

    def start(self, first_heard: str, context: dict) -> AgentTurn:
        t0 = time.perf_counter()
        r = self.client.post(f"{self.base}/calls", json={"first_heard": first_heard, "context": context})
        r.raise_for_status()
        body = r.json()
        self.session_id = body["session_id"]
        return _to_turn(body["turn"], (time.perf_counter() - t0) * 1000)

    def respond(self, heard: str) -> AgentTurn:
        t0 = time.perf_counter()
        r = self.client.post(f"{self.base}/calls/{self.session_id}/turns", json={"heard": heard})
        r.raise_for_status()
        return _to_turn(r.json()["turn"], (time.perf_counter() - t0) * 1000)
