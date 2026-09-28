"""Persona = a simulated caller with facts, a language and a behaviour style."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class PersonaSpec:
    """Loaded from the scenario YAML file."""

    name: str
    language: str = "en"                 # en | es | zh | hinglish
    style: str = "cooperative"           # cooperative | impatient | asks_human | kb_question | voicemail | refuses | rambler
    facts: dict[str, str] = field(default_factory=dict)  # ground truth the caller knows
    accent_noise: float = 0.0            # 0.0 - 1.0, how badly STT will mishear this caller
    interrupt_prob: float = 0.0          # chance the caller talks over the agent (barge-in)
    kb_question: str | None = None       # a question to ask mid-call


class Persona(ABC):
    """Interface every caller implementation follows."""

    def __init__(self, spec: PersonaSpec):
        self.spec = spec

    @abstractmethod
    def opening(self) -> str:
        """What the caller says when the call connects."""

    @abstractmethod
    def reply(self, agent_text: str) -> str | None:
        """Reply to the agent. Return None to stay silent / hang up."""
