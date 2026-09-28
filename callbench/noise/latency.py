"""Latency model for one voice turn.

Caller stops speaking -> agent starts speaking is the delay humans notice.
It is roughly:

    endpointing (STT decides the caller finished)
  + agent think time (LLM / logic)
  + TTS time-to-first-byte
  + network

We sample each part with a seeded RNG so results are reproducible.
"""
from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class LatencyBreakdown:
    endpointing_ms: float
    think_ms: float
    tts_ttfb_ms: float
    network_ms: float

    @property
    def total_ms(self) -> float:
        return self.endpointing_ms + self.think_ms + self.tts_ttfb_ms + self.network_ms


class LatencyModel:
    def __init__(self, seed: int = 0, endpointing_ms: float = 300, tts_ttfb_ms: float = 150,
                 network_ms: float = 60):
        self.rng = random.Random(seed)
        self.endpointing_ms = endpointing_ms
        self.tts_ttfb_ms = tts_ttfb_ms
        self.network_ms = network_ms

    def sample(self, think_ms: float, caller_words: int, accent_noise: float) -> LatencyBreakdown:
        # Long, hesitant or accented speech makes endpointing slower.
        endpoint = self.endpointing_ms + accent_noise * 350 + min(caller_words, 40) * 4
        endpoint *= self.rng.uniform(0.85, 1.3)
        tts = self.tts_ttfb_ms * self.rng.uniform(0.8, 1.6)
        net = self.network_ms * self.rng.uniform(0.7, 2.0)
        return LatencyBreakdown(endpoint, think_ms, tts, net)
