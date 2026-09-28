from fastapi.testclient import TestClient

from callbench.web import create_app

client = TestClient(create_app())


def test_index_and_static():
    assert "callbench" in client.get("/").text
    assert client.get("/static/app.js").status_code == 200


def test_scenario_lists_personas():
    names = [p["name"] for p in client.get("/api/scenario").json()["personas"]]
    assert "hinglish_hr" in names and len(names) == 12


def test_run_subset():
    r = client.post("/api/run", json={"personas": ["cooperative_hr", "voicemail_hinglish"], "runs_per_persona": 2})
    body = r.json()
    assert r.status_code == 200 and body["summary"]["calls"] == 4
    assert body["summary"]["by_persona"]["voicemail_hinglish"] == 0


def test_run_rejects_empty_and_huge():
    assert client.post("/api/run", json={"personas": ["nope"]}).status_code == 400
    assert client.post("/api/run", json={"runs_per_persona": 50}).status_code == 422


def test_chat_flow():
    s = client.post("/api/chat/start", json={"opening": "Hello?"}).json()
    assert "full name" in s["turn"]["text"]
    t = client.post(f"/api/chat/{s['session_id']}", json={"text": "Can I speak to a real person?"}).json()
    assert t["turn"]["action"] == "transfer"
    assert client.post("/api/chat/unknown", json={"text": "hi"}).status_code == 404
