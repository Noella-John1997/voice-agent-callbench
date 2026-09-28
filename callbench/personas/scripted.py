"""Deterministic, rule-based callers.

They look at what the agent just asked (name? dates? title?) and answer from
their facts, in their language, with their personality. No API key needed,
and the same seed always produces the same call, which makes regressions easy
to spot.
"""
from __future__ import annotations

import random
import re

from .base import Persona, PersonaSpec

# Canned phrases per language. Keys are "intents" the persona can express.
PHRASES: dict[str, dict[str, str]] = {
    "en": {
        "hello": "Hello?",
        "yes": "Yes, that's right.",
        "no": "No, that's not correct.",
        "name": "The employee's name is {employee_name}.",
        "dates": "They worked here from {start_date} to {end_date}.",
        "title": "Their job title was {job_title}.",
        "human": "Can I please speak to a real person?",
        "refuse": "I'm not comfortable sharing that. Please don't call again.",
        "bye": "Okay, thank you, bye.",
        "impatient": "Yeah yeah, just get to the point.",
        "ramble": "Well, you know, it's been a long week, anyway,",
        "voicemail": "Hi, you've reached the HR desk. Please leave a message after the tone.",
    },
    "es": {
        "hello": "¿Hola?",
        "yes": "Sí, es correcto.",
        "no": "No, eso no es correcto.",
        "name": "El nombre del empleado es {employee_name}.",
        "dates": "Trabajó aquí desde {start_date} hasta {end_date}.",
        "title": "Su puesto era {job_title}.",
        "human": "¿Puedo hablar con una persona, por favor?",
        "refuse": "No me siento cómodo compartiendo eso.",
        "bye": "Gracias, adiós.",
        "impatient": "Sí, sí, vaya al grano.",
        "ramble": "Bueno, pues, ha sido una semana larga,",
        "voicemail": "Ha llamado a Recursos Humanos. Deje su mensaje después del tono.",
    },
    "zh": {
        "hello": "喂？",
        "yes": "是的，没错。",
        "no": "不，不对。",
        "name": "员工的名字是 {employee_name}。",
        "dates": "他从 {start_date} 工作到 {end_date}。",
        "title": "他的职位是 {job_title}。",
        "human": "我可以和真人说话吗？",
        "refuse": "我不方便透露这些信息。",
        "bye": "好的，谢谢，再见。",
        "impatient": "快点说重点。",
        "ramble": "嗯，这周挺忙的，",
        "voicemail": "您好，这里是人事部，请在提示音后留言。",
    },
    # Code-switched Hindi + English, very common on Indian phone lines.
    "hinglish": {
        "hello": "Haan, hello?",
        "yes": "Haan ji, bilkul sahi hai.",
        "no": "Nahi, yeh galat hai.",
        "name": "Employee ka naam {employee_name} hai.",
        "dates": "Unhone {start_date} se {end_date} tak kaam kiya.",
        "title": "Unka designation {job_title} tha.",
        "human": "Kya main kisi insaan se baat kar sakta hoon?",
        "refuse": "Main yeh details share nahi kar sakta.",
        "bye": "Theek hai, dhanyavaad, bye.",
        "impatient": "Haan haan, jaldi boliye.",
        "ramble": "Arre, kya bataun, bahut busy week tha,",
        "voicemail": "Aapne HR desk ko call kiya hai. Beep ke baad message chhodiye.",
    },
}

# Words the agent might use when asking for each field, across languages.
# Latin words use \b word boundaries; Chinese has no spaces, so it is matched as-is.
ASK_PATTERNS = {
    "name": r"\b(name|nombre|naam)\b|名字",
    "dates": r"\b(dates?|when|fechas?|kab)\b|日期|时间",
    "title": r"\b(title|role|position|puesto|cargo|designation)\b|职位",
    # Only a read-back question counts ("...is that correct?"), not "calling to confirm".
    "confirm": r"(is that (correct|right)|¿es correcto|对吗|sahi hai\?)",
    "repeat": r"(repeat|say that again|repetir|再说一遍|dobara)",
    "goodbye": r"(goodbye|have a great day|adiós|再见|thank you for your time)",
}


class ScriptedPersona(Persona):
    def __init__(self, spec: PersonaSpec, seed: int = 0):
        super().__init__(spec)
        self.rng = random.Random(seed)
        self.lang = spec.language if spec.language in PHRASES else "en"
        self.asked_kb = False
        self.asked_human = False
        self.turns = 0
        self.last_answer: str | None = None

    # -- helpers -----------------------------------------------------------
    def _say(self, key: str) -> str:
        return PHRASES[self.lang][key].format(**self.spec.facts)

    def opening(self) -> str:
        if self.spec.style == "voicemail":
            return self._say("voicemail")
        return self._say("hello")

    def reply(self, agent_text: str) -> str | None:
        self.turns += 1
        style = self.spec.style
        text = agent_text.lower()

        if style == "voicemail":
            return None  # a voicemail box never answers

        if re.search(ASK_PATTERNS["goodbye"], text):
            return self._say("bye")

        if style == "refuses":
            return self._say("refuse")

        if style == "asks_human" and not self.asked_human:
            self.asked_human = True
            return self._say("human")

        if style == "kb_question" and not self.asked_kb and self.spec.kb_question:
            self.asked_kb = True
            return self.spec.kb_question

        prefix = ""
        if style == "impatient" and self.rng.random() < 0.5:
            prefix = self._say("impatient") + " "
        if style == "rambler":
            prefix = self._say("ramble") + " "

        # Agent asked us to repeat: say the last answer again (like a real person would).
        if re.search(ASK_PATTERNS["repeat"], text) and self.last_answer:
            return self.last_answer

        # Check "is that correct?" first: a read-back mentions name/dates/title too.
        if re.search(ASK_PATTERNS["confirm"], text):
            return prefix + self._say("yes")
        for intent in ("name", "dates", "title"):
            if re.search(ASK_PATTERNS[intent], text):
                self.last_answer = self._say(intent)
                return prefix + self.last_answer
        # Didn't understand the agent: a real caller would say "sorry?"
        return prefix + {"en": "Sorry, what?", "es": "¿Perdón?", "zh": "什么？", "hinglish": "Kya? Samjha nahi."}[self.lang]
