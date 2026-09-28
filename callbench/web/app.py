"""Web dashboard for callbench.

    callbench web            ->  http://127.0.0.1:8000

Two things you can do in the browser:
1. Run the test suite: pick personas, noise, seed, latency budget -> see the report live.
2. Call the demo agent yourself: type as a caller, see what STT "heard" and how the agent reacts.
"""
from __future__ import annotations

import copy
import os
import random
import time
import uuid
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ..metrics.scoring import summarize
from ..noise import ASRNoise, LatencyModel
from ..runner.suite import Scenario, load_scenario, run_suite
from ..targets import DemoVerificationAgent

STATIC = Path(__file__).with_name("static")
DEFAULT_SCENARIO = Path(__file__).resolve().parents[2] / "scenarios" / "employment_verification.yaml"
MAX_CALLS = 200            # protects a public demo from huge runs
CHAT_TTL_SECONDS = 1800


class RunRequest(BaseModel):
    personas: list[str] | None = None          # None = all
    seed: int = 7
    runs_per_persona: int = Field(3, ge=1, le=10)
    latency_budget_ms: float = Field(1200, ge=100, le=10000)
    extra_noise: float = Field(0.0, ge=0, le=1)     # added to every persona's accent_noise
    extra_interrupts: float = Field(0.0, ge=0, le=1)


class ChatStart(BaseModel):
    opening: str = "Hello?"
    noise: float = Field(0.0, ge=0, le=1)
    seed: int = 1


class ChatTurn(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)


def _turn_json(t, latency_ms: float) -> dict:
    d = asdict(t)
    d["action"] = t.action.value
    d["latency_ms"] = round(latency_ms, 1)
    return d


def create_app(scenario_path: str | Path | None = None) -> FastAPI:
    path = Path(scenario_path or os.getenv("CALLBENCH_SCENARIO", DEFAULT_SCENARIO))
    base: Scenario = load_scenario(path)
    chats: dict[str, dict] = {}

    app = FastAPI(title="callbench", description="Synthetic-caller testing for voice agents")
    app.mount("/static", StaticFiles(directory=STATIC), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC / "index.html")

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.get("/api/scenario")
    def scenario():
        return {"id": base.id, "description": base.description, "runs_per_persona": base.runs_per_persona,
                "personas": [{"name": s.name, "language": s.language, "style": s.style,
                              "accent_noise": s.accent_noise, "interrupt_prob": s.interrupt_prob,
                              "expect": e.outcome} for s, e in base.personas]}

    @app.post("/api/run")
    def run(req: RunRequest):
        sc = copy.deepcopy(base)
        if req.personas:
            sc.personas = [(s, e) for s, e in sc.personas if s.name in set(req.personas)]
        if not sc.personas:
            raise HTTPException(400, "pick at least one persona")
        if len(sc.personas) * req.runs_per_persona > MAX_CALLS:
            raise HTTPException(400, f"too many calls (max {MAX_CALLS})")
        sc.runs_per_persona = req.runs_per_persona
        for spec, exp in sc.personas:
            spec.accent_noise = min(1.0, spec.accent_noise + req.extra_noise)
            spec.interrupt_prob = min(1.0, spec.interrupt_prob + req.extra_interrupts)
            exp.max_p95_latency_ms = req.latency_budget_ms
        t0 = time.perf_counter()
        results = run_suite(sc, target="demo", seed=req.seed)
        return {"summary": summarize(results), "elapsed_ms": round((time.perf_counter() - t0) * 1000, 1),
                "calls": [r.to_dict() for r in results]}

    # ------------------------------------------------ talk to the agent yourself
    def _gc():
        now = time.time()
        for k in [k for k, v in chats.items() if now - v["ts"] > CHAT_TTL_SECONDS]:
            chats.pop(k, None)

    @app.post("/api/chat/start")
    def chat_start(req: ChatStart):
        _gc()
        sid = uuid.uuid4().hex
        agent = DemoVerificationAgent(seed=req.seed)
        stt = ASRNoise(req.noise, seed=req.seed)
        lat = LatencyModel(seed=req.seed)
        heard = stt.apply(req.opening)
        turn = agent.start(heard, {})
        chats[sid] = {"agent": agent, "stt": stt, "lat": lat, "noise": req.noise, "ts": time.time()}
        ms = lat.sample(turn.think_ms, len(heard.split()), req.noise).total_ms
        return {"session_id": sid, "heard_as": heard, "turn": _turn_json(turn, ms)}

    @app.post("/api/chat/{sid}")
    def chat_turn(sid: str, req: ChatTurn):
        c = chats.get(sid)
        if not c:
            raise HTTPException(404, "session expired — start a new call")
        c["ts"] = time.time()
        heard = c["stt"].apply(req.text)
        turn = c["agent"].respond(heard)
        ms = c["lat"].sample(turn.think_ms, len(heard.split()), c["noise"]).total_ms
        return {"heard_as": heard, "turn": _turn_json(turn, ms)}

    return app


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    import uvicorn
    uvicorn.run(create_app(), host=host, port=port)
