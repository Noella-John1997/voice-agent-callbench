from callbench.personas import PersonaSpec, ScriptedPersona
from callbench.runner import simulate_call
from callbench.targets import DemoVerificationAgent
from callbench.types import Expectation

FACTS = {"employee_name": "Priya Sharma", "start_date": "March 2019",
         "end_date": "June 2023", "job_title": "Senior Data Analyst"}


def _run(spec, expected, seed=1):
    return simulate_call("t", ScriptedPersona(spec, seed=seed), DemoVerificationAgent(seed=seed),
                         expected, seed=seed)


def test_cooperative_call_verifies():
    r = _run(PersonaSpec("coop", facts=FACTS), Expectation("verified", FACTS, 5000))
    assert r.actual_outcome == "verified"
    assert r.checks["fields_correct"]
    assert r.passed


def test_hinglish_voicemail_is_a_known_gap():
    # The demo agent does not understand Hinglish voicemail greetings.
    # callbench should catch that and FAIL the call.
    r = _run(PersonaSpec("vm", language="hinglish", style="voicemail", facts=FACTS),
             Expectation("voicemail_drop"))
    assert not r.passed
    assert r.actual_outcome != "voicemail_drop"


def test_latency_budget_check_fails_when_too_strict():
    r = _run(PersonaSpec("coop", facts=FACTS), Expectation("verified", FACTS, max_p95_latency_ms=10))
    assert r.checks["latency_ok"] is False
    assert not r.passed
