"""Shared data types used across callbench.

Everything is a plain dataclass so results can be dumped to JSON easily.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


class Action(str, Enum):
    """What the agent does at the end of a turn."""

    CONTINUE = "continue"          # keep talking
    TRANSFER = "transfer"          # hand the call to a human
    HANGUP = "hangup"              # end the call
    VOICEMAIL_DROP = "voicemail_drop"  # leave a voicemail message and end


@dataclass
class AgentTurn:
    """One reply from the agent under test."""

    text: str
    action: Action = Action.CONTINUE
    extracted: dict[str, str] = field(default_factory=dict)
    # Time the agent's own logic took (LLM / business logic), in milliseconds.
    think_ms: float = 0.0
    language: str = "en"


@dataclass
class TurnRecord:
    """One exchange as recorded by the simulator."""

    index: int
    speaker: str                  # "agent" or "caller"
    text: str                     # what was actually said
    heard_as: str | None = None   # for caller turns: what the agent's STT "heard"
    latency_ms: float | None = None  # for agent turns: caller-stops -> agent-starts
    barge_in: bool = False
    action: str | None = None


@dataclass
class Expectation:
    """What a correct agent should achieve on this call."""

    outcome: str                                   # "verified" | "transfer" | "voicemail_drop" | "hangup"
    fields: dict[str, str] = field(default_factory=dict)  # values the agent must extract
    max_p95_latency_ms: float = 1200.0


@dataclass
class CallResult:
    scenario_id: str
    persona: str
    language: str
    expected: Expectation
    actual_outcome: str
    extracted: dict[str, str]
    transcript: list[TurnRecord]
    checks: dict[str, bool]
    latency_p50_ms: float
    latency_p95_ms: float
    wer: float
    passed: bool
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d
