"""Optional: let a real LLM play the caller.

Scripted personas are predictable; an LLM persona is closer to a messy human.
Enabled with `--llm-personas` when OPENAI_API_KEY is set (any OpenAI-compatible
endpoint works, e.g. a local vLLM or Ollama server via OPENAI_BASE_URL).
"""
from __future__ import annotations

from ..llm.providers import ChatLLM
from .base import Persona, PersonaSpec
from .scripted import PHRASES

SYSTEM_TEMPLATE = """You are role-playing a person who has just answered a phone call.
Stay in character. Reply with ONE short spoken sentence, no stage directions.
Language: {language}. Personality: {style}.
Facts you know (only share them if asked): {facts}.
{extra}"""


class LLMPersona(Persona):
    def __init__(self, spec: PersonaSpec, llm: ChatLLM):
        super().__init__(spec)
        self.llm = llm
        extra = ""
        if spec.style == "asks_human":
            extra = "Early in the call, insist on talking to a human."
        if spec.style == "kb_question" and spec.kb_question:
            extra = f"At some point ask: '{spec.kb_question}'"
        if spec.style == "refuses":
            extra = "Politely refuse to share any information."
        self.messages = [{
            "role": "system",
            "content": SYSTEM_TEMPLATE.format(
                language=spec.language, style=spec.style, facts=spec.facts, extra=extra
            ),
        }]

    def opening(self) -> str:
        lang = self.spec.language if self.spec.language in PHRASES else "en"
        if self.spec.style == "voicemail":
            return PHRASES[lang]["voicemail"]
        return PHRASES[lang]["hello"]

    def reply(self, agent_text: str) -> str | None:
        if self.spec.style == "voicemail":
            return None
        self.messages.append({"role": "user", "content": agent_text})
        answer = self.llm.chat(self.messages).strip()
        self.messages.append({"role": "assistant", "content": answer})
        return answer
