"""Simulate speech-to-text mistakes.

Real STT engines mishear callers with strong accents, bad lines or background
noise. We copy the most common error types seen in call-centre transcripts:

* substitutions of similar-sounding words ("fifteen" -> "fifty")
* dropped short words ("the", "a", "to")
* digits mangled ("2019" -> "2090")
"""
from __future__ import annotations

import random
import re

# Sound-alike confusions frequently seen in phone-quality (8 kHz) audio.
CONFUSIONS = {
    "fifteen": "fifty", "sixteen": "sixty", "thirteen": "thirty",
    "march": "much", "may": "me", "june": "jean", "july": "julie",
    "engineer": "engine ear", "manager": "man a jar", "analyst": "and a list",
    "right": "write", "correct": "collect", "name": "nine",
    "to": "two", "from": "form", "their": "there",
    "priya": "pria", "sharma": "sharmer", "garcia": "gracia", "chen": "chan",
}
FILLER = {"the", "a", "an", "to", "of", "is"}


class ASRNoise:
    def __init__(self, level: float, seed: int = 0):
        """level: 0.0 = perfect transcript, 1.0 = very noisy."""
        self.level = max(0.0, min(1.0, level))
        self.rng = random.Random(seed)

    def _mangle_number(self, token: str) -> str:
        digits = list(token)
        i = self.rng.randrange(len(digits))
        digits[i] = str(self.rng.randrange(10))
        return "".join(digits)

    def apply(self, text: str) -> str:
        if self.level == 0 or not text:
            return text
        out: list[str] = []
        for word in text.split():
            core = re.sub(r"[^\w]", "", word).lower()
            r = self.rng.random()
            if core in CONFUSIONS and r < self.level * 0.6:
                out.append(CONFUSIONS[core])
            elif core in FILLER and r < self.level * 0.3:
                continue  # dropped
            elif core.isdigit() and r < self.level * 0.25:
                out.append(self._mangle_number(core))
            else:
                out.append(word)
        return " ".join(out)
