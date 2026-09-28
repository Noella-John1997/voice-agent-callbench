"""Runs ONE simulated phone call between a persona and an agent.

Loop:
    caller speaks -> STT noise -> agent thinks -> latency sampled -> agent speaks
    (maybe the caller barges in and only hears half) -> caller replies -> ...
until the agent transfers, hangs up, drops a voicemail, or max_turns is hit.
"""
from __future__ import annotations

import random

from ..metrics.scoring import score_call
from ..noise import ASRNoise, LatencyModel
from ..personas.base import Persona
from ..targets.base import Target
from ..types import Action, CallResult, Expectation, TurnRecord


def _outcome(action: Action, extracted: dict[str, str], required: list[str]) -> str:
    if action == Action.TRANSFER:
        return "transfer"
    if action == Action.VOICEMAIL_DROP:
        return "voicemail_drop"
    if action == Action.HANGUP:
        if required and all(extracted.get(f) for f in required):
            return "verified"
        return "hangup"
    return "no_resolution"  # ran out of turns


def simulate_call(
    scenario_id: str,
    persona: Persona,
    agent: Target,
    expected: Expectation,
    seed: int = 0,
    max_turns: int = 16,
    latency_model: LatencyModel | None = None,
) -> CallResult:
    spec = persona.spec
    rng = random.Random(seed)
    stt = ASRNoise(spec.accent_noise, seed=seed)
    lat = latency_model or LatencyModel(seed=seed)

    transcript: list[TurnRecord] = []
    latencies: list[float] = []
    clean_caller: list[str] = []
    heard_caller: list[str] = []
    idx = 0

    said = persona.opening()
    heard = stt.apply(said)
    transcript.append(TurnRecord(idx, "caller", said, heard_as=heard)); idx += 1
    clean_caller.append(said); heard_caller.append(heard)

    turn = agent.start(heard, {"language_hint": None, "seed": seed})
    notes: list[str] = []

    for _ in range(max_turns):
        l = lat.sample(turn.think_ms, len(heard.split()), spec.accent_noise).total_ms
        latencies.append(l)

        barge = turn.action == Action.CONTINUE and rng.random() < spec.interrupt_prob
        agent_text_heard_by_caller = turn.text
        if barge:
            words = turn.text.split()
            agent_text_heard_by_caller = " ".join(words[: max(1, len(words) // 2)])
        transcript.append(TurnRecord(idx, "agent", turn.text, latency_ms=round(l, 1),
                                     barge_in=barge, action=turn.action.value)); idx += 1

        if turn.action != Action.CONTINUE:
            break

        said = persona.reply(agent_text_heard_by_caller)
        if said is None:
            notes.append("caller went silent")
            break
        heard = stt.apply(said)
        transcript.append(TurnRecord(idx, "caller", said, heard_as=heard)); idx += 1
        clean_caller.append(said); heard_caller.append(heard)
        turn = agent.respond(heard)
    else:
        notes.append(f"hit max_turns={max_turns}")

    required = list(expected.fields.keys())
    outcome = _outcome(turn.action, turn.extracted, required)
    return score_call(
        scenario_id=scenario_id, persona=spec.name, language=spec.language,
        expected=expected, actual_outcome=outcome, extracted=turn.extracted,
        transcript=transcript, latencies=latencies,
        clean_caller=clean_caller, heard_caller=heard_caller, notes=notes,
    )
