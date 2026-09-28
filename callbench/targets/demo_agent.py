"""A small reference employment-verification agent.

It mirrors the flow of a production verification agent:
greet -> ask name -> ask dates -> ask title -> confirm -> goodbye,
with voicemail drop, human transfer, a tiny knowledge base and 3 languages.

It is intentionally imperfect (for example it does not understand Hinglish and
it trusts whatever STT heard) so that callbench has real bugs to find. Swap it
for your own agent via the HTTP target.
"""
from __future__ import annotations

import random
import re

from ..types import Action, AgentTurn

T = {
    "en": {
        "greet": "Hi, this is Ava, an automated assistant from Acme Verify calling to confirm employment details. What is the employee's full name?",
        "ask_name": "What is the employee's full name?",
        "ask_dates": "Thanks. What were their employment dates?",
        "ask_title": "Got it. What was their job title?",
        "confirm": "To confirm: {employee_name}, from {start_date} to {end_date}, as {job_title}. Is that correct?",
        "bye": "Thank you for your time. Have a great day, goodbye.",
        "repeat": "Sorry, I didn't catch that. Could you repeat the {field}?",
        "transfer": "Of course, let me transfer you to a member of our team now.",
        "voicemail": "Hi, this is Acme Verify calling about an employment verification. Please call us back at 555-0100. Thank you.",
        "refused": "I understand. Thank you for your time, goodbye.",
    },
    "es": {
        "greet": "Hola, soy Ava, asistente automática de Acme Verify, llamo para confirmar datos de empleo. ¿Cuál es el nombre del empleado?",
        "ask_name": "¿Cuál es el nombre del empleado?",
        "ask_dates": "Gracias. ¿Cuáles fueron las fechas de empleo?",
        "ask_title": "Entendido. ¿Cuál era su puesto?",
        "confirm": "Para confirmar: {employee_name}, desde {start_date} hasta {end_date}, como {job_title}. ¿Es correcto?",
        "bye": "Gracias por su tiempo. Adiós.",
        "repeat": "Perdón, no le entendí. ¿Puede repetir el dato?",
        "transfer": "Claro, le transfiero con una persona de nuestro equipo.",
        "voicemail": "Hola, llamamos de Acme Verify por una verificación de empleo. Llámenos al 555-0100. Gracias.",
        "refused": "Entiendo. Gracias por su tiempo, adiós.",
    },
    "zh": {
        "greet": "您好，我是 Acme Verify 的自动助理 Ava，来电确认雇佣信息。请问员工的名字是什么？",
        "ask_name": "请问员工的名字是什么？",
        "ask_dates": "谢谢。请问他的工作日期是什么时间？",
        "ask_title": "好的。请问他的职位是什么？",
        "confirm": "确认一下：{employee_name}，从 {start_date} 到 {end_date}，职位 {job_title}，对吗？",
        "bye": "感谢您的时间，再见。",
        "repeat": "抱歉，我没听清，请再说一遍。",
        "transfer": "好的，我现在为您转接人工客服。",
        "voicemail": "您好，这里是 Acme Verify，关于雇佣核实，请回电 555-0100。谢谢。",
        "refused": "我理解，感谢您的时间，再见。",
    },
}

EXTRACT = {
    "en": {
        "employee_name": r"name is ([A-Za-z][A-Za-z .'-]+?)[.,]?$",
        "dates": r"from (.+?) (?:to|two) (.+?)\.?$",
        "job_title": r"title was (.+?)\.?$",
    },
    "es": {
        "employee_name": r"nombre del empleado es (.+?)\.?$",
        "dates": r"desde (.+?) hasta (.+?)\.?$",
        "job_title": r"puesto era (.+?)\.?$",
    },
    "zh": {
        "employee_name": r"名字是\s*(.+?)。?$",
        "dates": r"从\s*(.+?)\s*工作到\s*(.+?)。?$",
        "job_title": r"职位是\s*(.+?)。?$",
    },
}

VOICEMAIL_CUES = ["leave a message", "after the tone", "deje su mensaje", "留言"]
HUMAN_CUES = ["real person", "human", "representative", "una persona", "真人"]
REFUSAL_CUES = ["not comfortable", "don't call", "no me siento", "不方便"]
YES_CUES = ["yes", "correct", "right", "sí", "correcto", "是的", "对"]
KB = {
    ("what company", "who is calling", "who are you"): "I'm calling from Acme Verify, a background verification service.",
    ("why", "purpose"): "We're verifying employment details that the candidate has authorised us to check.",
    ("recorded", "recording"): "Yes, this call may be recorded for quality and compliance.",
}


class DemoVerificationAgent:
    def __init__(self, seed: int = 0):
        self.rng = random.Random(seed)
        self.lang = "en"
        self.state = "greet"
        self.data: dict[str, str] = {}
        self.retries = 0

    # -- internal helpers --------------------------------------------------
    def _turn(self, key: str, action: Action = Action.CONTINUE, **fmt) -> AgentTurn:
        text = T[self.lang][key].format(**{**self.data, **fmt})
        # Simulated time-to-first-token of a streaming LLM: base + small per-word cost.
        # Mandarin is slower because it uses more tokens per sentence.
        think = 240 + 2 * len(text.split()) + (180 if self.lang == "zh" else 0)
        think *= self.rng.uniform(0.8, 1.4)
        return AgentTurn(text=text, action=action, extracted=dict(self.data), think_ms=think, language=self.lang)

    @staticmethod
    def _has(text: str, cues: list[str]) -> bool:
        low = text.lower()
        return any(c in low for c in cues)

    def _detect_lang(self, text: str) -> str:
        if re.search(r"[一-鿿]", text):
            return "zh"
        if re.search(r"[¿¡ñáéíóú]|\bhola\b", text.lower()):
            return "es"
        return "en"  # NOTE: Hinglish falls through to English (known gap)

    def _extract(self, field: str, heard: str) -> bool:
        m = re.search(EXTRACT[self.lang][field], heard.strip(), flags=re.IGNORECASE)
        if not m:
            return False
        if field == "dates":
            self.data["start_date"], self.data["end_date"] = m.group(1).strip(), m.group(2).strip()
        else:
            self.data[field] = m.group(1).strip()
        return True

    # -- Target interface --------------------------------------------------
    def start(self, first_heard: str, context: dict) -> AgentTurn:
        self.lang = context.get("language_hint") or self._detect_lang(first_heard)
        if self.lang not in T:
            self.lang = "en"
        if self._has(first_heard, VOICEMAIL_CUES):
            self.state = "done"
            return self._turn("voicemail", Action.VOICEMAIL_DROP)
        self.state = "ask_name"
        return self._turn("greet")

    def respond(self, heard: str) -> AgentTurn:
        if self._has(heard, HUMAN_CUES):
            return self._turn("transfer", Action.TRANSFER)
        if self._has(heard, REFUSAL_CUES):
            return self._turn("refused", Action.HANGUP)
        for keys, answer in KB.items():
            if any(k in heard.lower() for k in keys):
                # Answer from the knowledge base, then re-ask the pending question.
                pending = self._turn(self.state if self.state in T[self.lang] else "bye")
                pending.text = f"{answer} {pending.text}"
                return pending

        field_for_state = {"ask_name": "employee_name", "ask_dates": "dates", "ask_title": "job_title"}
        next_state = {"ask_name": "ask_dates", "ask_dates": "ask_title", "ask_title": "confirm"}

        if self.state in field_for_state:
            field = field_for_state[self.state]
            if self._extract(field, heard):
                self.retries = 0
                self.state = next_state[self.state]
                return self._turn(self.state)
            self.retries += 1
            if self.retries >= 2:  # escalate instead of looping forever
                return self._turn("transfer", Action.TRANSFER)
            return self._turn("repeat", field=field.replace("_", " "))

        if self.state == "confirm":
            if self._has(heard, YES_CUES):
                self.state = "done"
                return self._turn("bye", Action.HANGUP)
            return self._turn("transfer", Action.TRANSFER)

        return self._turn("bye", Action.HANGUP)
