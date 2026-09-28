from fastapi.testclient import TestClient

from callbench.targets import HTTPTarget
from callbench.targets.demo_server import app
from callbench.types import Action


def test_http_contract_round_trip():
    target = HTTPTarget("http://testserver", client=TestClient(app))
    t = target.start("Hello?", {"seed": 1})
    assert t.action == Action.CONTINUE and target.session_id
    t = target.respond("Can I speak to a real person?")
    assert t.action == Action.TRANSFER
