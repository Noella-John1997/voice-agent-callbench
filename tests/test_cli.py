import json

from callbench.cli import main
from conftest import SCENARIO


def test_run_writes_reports(tmp_path):
    code = main(["run", str(SCENARIO), "--out", str(tmp_path)])
    assert code == 0
    data = json.loads((tmp_path / "results.json").read_text())
    assert data["summary"]["calls"] == 36
    assert (tmp_path / "report.html").exists()


def test_fail_under_gate_returns_1(tmp_path):
    assert main(["run", str(SCENARIO), "--out", str(tmp_path), "--fail-under", "0.99"]) == 1


def test_baseline_delta(tmp_path):
    main(["run", str(SCENARIO), "--out", str(tmp_path / "a")])
    main(["run", str(SCENARIO), "--out", str(tmp_path / "b"), "--baseline", str(tmp_path / "a" / "results.json")])
    data = json.loads((tmp_path / "b" / "results.json").read_text())
    assert data["baseline_delta"]["pass_rate"] == 0
