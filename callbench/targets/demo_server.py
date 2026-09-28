"""FastAPI server exposing DemoVerificationAgent over the HTTP contract."""
from __future__ import annotations

import uuid
from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .demo_agent import DemoVerificationAgent

app = FastAPI(title="callbench demo verification agent")
SESSIONS: dict[str, DemoVerificationAgent] = {}


class StartBody(BaseModel):
    first_heard: str
    context: dict = {}


class TurnBody(BaseModel):
    heard: str


def _dump(turn) -> dict:
    d = asdict(turn)
    d["action"] = turn.action.value
    return d


@app.post("/calls")
def start_call(body: StartBody):
    sid = uuid.uuid4().hex
    agent = DemoVerificationAgent(seed=body.context.get("seed", 0))
    SESSIONS[sid] = agent
    return {"session_id": sid, "turn": _dump(agent.start(body.first_heard, body.context))}


@app.post("/calls/{sid}/turns")
def turn(sid: str, body: TurnBody):
    agent = SESSIONS.get(sid)
    if agent is None:
        raise HTTPException(404, "unknown session")
    return {"turn": _dump(agent.respond(body.heard))}


@app.get("/health")
def health():
    return {"ok": True, "active_sessions": len(SESSIONS)}
