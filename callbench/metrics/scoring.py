"""Scoring: turns a raw transcript into pass/fail checks and numbers."""
from __future__ import annotations

import math
import re
from collections import defaultdict

from ..types import CallResult, Expectation, TurnRecord


def _tokens(text: str) -> list[str]:
    # Chinese has no spaces: score it per character, everything else per word.
    if re.search(r"[一-鿿]", text):
        return [c for c in text if not c.isspace() and c not in "，。？！,.?!"]
    return re.sub(r"[^\w\s]", " ", text.lower()).split()


def word_error_rate(reference: str, hypothesis: str) -> float:
    """Classic WER = (substitutions + deletions + insertions) / reference words.

    Computed with edit distance (dynamic programming), O(n*m).
    """
    ref, hyp = _tokens(reference), _tokens(hypothesis)
    if not ref:
        return 0.0 if not hyp else 1.0
    prev = list(range(len(hyp) + 1))
    for i in range(1, len(ref) + 1):
        cur = [i] + [0] * len(hyp)
        for j in range(1, len(hyp) + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[-1] / len(ref)


def percentile(values: list[float], p: float) -> float:
    """Nearest-rank percentile (p in 0..100)."""
    if not values:
        return 0.0
    s = sorted(values)
    k = max(0, min(len(s) - 1, math.ceil(p / 100 * len(s)) - 1))
    return s[k]


def _norm(v: str) -> str:
    return re.sub(r"[^\w]", "", str(v).lower())


def score_call(*, scenario_id: str, persona: str, language: str, expected: Expectation,
               actual_outcome: str, extracted: dict[str, str], transcript: list[TurnRecord],
               latencies: list[float], clean_caller: list[str], heard_caller: list[str],
               notes: list[str]) -> CallResult:
    p50, p95 = percentile(latencies, 50), percentile(latencies, 95)
    wer = word_error_rate(" ".join(clean_caller), " ".join(heard_caller))

    checks = {"outcome_correct": actual_outcome == expected.outcome}
    if expected.outcome == "verified":
        wrong = [f for f, v in expected.fields.items() if _norm(extracted.get(f, "")) != _norm(v)]
        checks["fields_correct"] = not wrong
        if wrong:
            notes = notes + [f"wrong/missing fields: {', '.join(wrong)}"]
    checks["latency_ok"] = p95 <= expected.max_p95_latency_ms
    checks["no_loop"] = not any("max_turns" in n for n in notes)

    return CallResult(
        scenario_id=scenario_id, persona=persona, language=language, expected=expected,
        actual_outcome=actual_outcome, extracted=extracted, transcript=transcript, checks=checks,
        latency_p50_ms=round(p50, 1), latency_p95_ms=round(p95, 1), wer=round(wer, 3),
        passed=all(checks.values()), notes=notes,
    )


def summarize(results: list[CallResult]) -> dict:
    """Aggregate numbers for the report header and CI gates."""
    if not results:
        return {"calls": 0, "pass_rate": 0.0}
    all_lat = [t.latency_ms for r in results for t in r.transcript if t.latency_ms is not None]
    by_persona: dict[str, list[CallResult]] = defaultdict(list)
    by_lang: dict[str, list[CallResult]] = defaultdict(list)
    for r in results:
        by_persona[r.persona].append(r)
        by_lang[r.language].append(r)

    def rate(rs: list[CallResult]) -> float:
        return round(sum(r.passed for r in rs) / len(rs), 3)

    failed_checks: dict[str, int] = defaultdict(int)
    for r in results:
        for k, ok in r.checks.items():
            if not ok:
                failed_checks[k] += 1

    return {
        "calls": len(results),
        "pass_rate": rate(results),
        "latency_p50_ms": round(percentile(all_lat, 50), 1),
        "latency_p95_ms": round(percentile(all_lat, 95), 1),
        "mean_wer": round(sum(r.wer for r in results) / len(results), 3),
        "barge_ins": sum(t.barge_in for r in results for t in r.transcript),
        "by_persona": {k: rate(v) for k, v in sorted(by_persona.items())},
        "by_language": {k: rate(v) for k, v in sorted(by_lang.items())},
        "failed_checks": dict(failed_checks),
    }
