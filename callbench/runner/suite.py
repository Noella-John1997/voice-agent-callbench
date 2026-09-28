"""Runs every persona in a scenario file N times and collects results."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import yaml

from ..llm.providers import llm_from_env
from ..personas import PersonaSpec, ScriptedPersona
from ..personas.llm_persona import LLMPersona
from ..targets import DemoVerificationAgent, HTTPTarget
from ..targets.base import Target
from ..types import CallResult, Expectation
from .simulator import simulate_call


@dataclass
class Scenario:
    id: str
    description: str
    runs_per_persona: int
    max_turns: int
    personas: list[tuple[PersonaSpec, Expectation]]


def load_scenario(path: str | Path) -> Scenario:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    personas = []
    for p in raw["personas"]:
        exp = p.pop("expect")
        facts = {**raw.get("default_facts", {}), **p.pop("facts", {})}
        spec = PersonaSpec(facts=facts, **p)
        fields = {k: facts[k] for k in exp.get("fields", [])}
        personas.append((spec, Expectation(outcome=exp["outcome"], fields=fields,
                                           max_p95_latency_ms=exp.get("max_p95_latency_ms",
                                                                      raw.get("max_p95_latency_ms", 1200)))))
    return Scenario(
        id=raw["id"], description=raw.get("description", ""),
        runs_per_persona=raw.get("runs_per_persona", 1), max_turns=raw.get("max_turns", 16),
        personas=personas,
    )


def make_target_factory(target: str) -> Callable[[int], Target]:
    if target == "demo":
        return lambda seed: DemoVerificationAgent(seed=seed)
    if target.startswith("http"):
        return lambda seed: HTTPTarget(target)
    raise ValueError(f"unknown target '{target}' (use 'demo' or an http(s):// URL)")


def run_suite(scenario: Scenario, target: str = "demo", seed: int = 7,
              use_llm_personas: bool = False, progress: Callable[[CallResult], None] | None = None
              ) -> list[CallResult]:
    factory = make_target_factory(target)
    llm = llm_from_env() if use_llm_personas else None
    if use_llm_personas and llm is None:
        raise RuntimeError("--llm-personas needs OPENAI_API_KEY in the environment")
    results: list[CallResult] = []
    for spec, expected in scenario.personas:
        for run in range(scenario.runs_per_persona):
            s = seed * 1000 + run
            persona = LLMPersona(spec, llm) if llm else ScriptedPersona(spec, seed=s)
            res = simulate_call(scenario.id, persona, factory(s), expected, seed=s,
                                max_turns=scenario.max_turns)
            results.append(res)
            if progress:
                progress(res)
    return results
