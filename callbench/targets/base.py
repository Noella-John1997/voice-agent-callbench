"""The contract an agent under test must follow.

Wrap your own voice agent's *text brain* in this interface (or expose it over
HTTP, see http_target.py) and callbench can test it.
"""
from __future__ import annotations

from typing import Callable, Protocol

from ..types import AgentTurn


class Target(Protocol):
    def start(self, first_heard: str, context: dict) -> AgentTurn:
        """Call connected. `first_heard` is what STT heard (e.g. 'Hello?' or a voicemail greeting)."""

    def respond(self, heard: str) -> AgentTurn:
        """Caller said something (already passed through simulated STT)."""


# A factory returns a *fresh* agent for each call, so calls don't share state.
TargetFactory = Callable[[], Target]
