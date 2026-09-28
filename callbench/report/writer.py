"""Writes results.json (machine-readable) and report.html (for humans)."""
from __future__ import annotations

import html
import json
from pathlib import Path

from ..metrics.scoring import summarize
from ..types import CallResult


def compare_to_baseline(summary: dict, baseline_path: str | Path) -> dict:
    """Return the change in key numbers vs. a previous results.json."""
    base = json.loads(Path(baseline_path).read_text())["summary"]
    keys = ["pass_rate", "latency_p50_ms", "latency_p95_ms", "mean_wer"]
    return {k: round(summary.get(k, 0) - base.get(k, 0), 3) for k in keys}


def _badge(ok: bool) -> str:
    return f'<span class="b {"ok" if ok else "bad"}">{"PASS" if ok else "FAIL"}</span>'


def _rows(d: dict) -> str:
    return "".join(f"<tr><td>{html.escape(k)}</td><td>{v:.0%}</td></tr>" for k, v in d.items())


def write_reports(results: list[CallResult], out_dir: str | Path, title: str,
                  baseline_delta: dict | None = None) -> tuple[Path, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    summary = summarize(results)
    payload = {"title": title, "summary": summary, "baseline_delta": baseline_delta,
               "calls": [r.to_dict() for r in results]}
    json_path = out / "results.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    call_blocks = []
    for i, r in enumerate(results):
        lines = []
        for t in r.transcript:
            who = "Agent" if t.speaker == "agent" else "Caller"
            extra = ""
            if t.speaker == "caller" and t.heard_as and t.heard_as != t.text:
                extra = f'<div class="heard">STT heard: {html.escape(t.heard_as)}</div>'
            if t.latency_ms is not None:
                extra += f'<div class="meta">{t.latency_ms:.0f} ms{" · barge-in" if t.barge_in else ""}{" · " + t.action if t.action and t.action != "continue" else ""}</div>'
            lines.append(f'<div class="t {t.speaker}"><b>{who}:</b> {html.escape(t.text)}{extra}</div>')
        checks = " ".join(f'{k} {"✔" if v else "✘"}' for k, v in r.checks.items())
        call_blocks.append(
            f'<details><summary>{_badge(r.passed)} #{i+1} <b>{html.escape(r.persona)}</b> ({r.language}) '
            f'— expected <i>{r.expected.outcome}</i>, got <i>{r.actual_outcome}</i> · p95 {r.latency_p95_ms:.0f} ms · WER {r.wer:.0%}</summary>'
            f'<div class="checks">{checks}</div>'
            f'<div class="notes">{html.escape("; ".join(r.notes))}</div>'
            f'{"".join(lines)}</details>')

    delta_html = ""
    if baseline_delta:
        delta_html = "<p><b>vs. baseline:</b> " + ", ".join(f"{k} {v:+}" for k, v in baseline_delta.items()) + "</p>"

    s = summary
    page = f"""<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{{font-family:system-ui,sans-serif;max-width:1000px;margin:24px auto;padding:0 16px;color:#1c1c1c;background:#fafafa}}
.kpis{{display:flex;gap:12px;flex-wrap:wrap}} .k{{background:#fff;border:1px solid #ddd;border-radius:8px;padding:12px 16px}}
.k b{{display:block;font-size:22px}} table{{border-collapse:collapse;margin:8px 16px 8px 0;display:inline-table}}
td{{border-bottom:1px solid #eee;padding:4px 12px}} details{{background:#fff;border:1px solid #ddd;border-radius:8px;margin:8px 0;padding:8px 12px}}
.b{{font-size:11px;padding:2px 6px;border-radius:4px;color:#fff}} .ok{{background:#1a7f37}} .bad{{background:#cf222e}}
.t{{padding:6px 8px;margin:4px 0;border-radius:6px}} .agent{{background:#eef4ff}} .caller{{background:#f4f4f4}}
.heard{{color:#9a6700;font-size:12px}} .meta,.checks,.notes{{color:#666;font-size:12px}}
</style></head><body>
<h1>{html.escape(title)}</h1>
<div class="kpis">
<div class="k">Calls<b>{s['calls']}</b></div><div class="k">Pass rate<b>{s['pass_rate']:.0%}</b></div>
<div class="k">p50 latency<b>{s['latency_p50_ms']:.0f} ms</b></div><div class="k">p95 latency<b>{s['latency_p95_ms']:.0f} ms</b></div>
<div class="k">Mean simulated WER<b>{s['mean_wer']:.0%}</b></div><div class="k">Barge-ins<b>{s['barge_ins']}</b></div>
</div>{delta_html}
<h2>Pass rate</h2>
<table><tr><th colspan=2>By persona</th></tr>{_rows(s['by_persona'])}</table>
<table><tr><th colspan=2>By language</th></tr>{_rows(s['by_language'])}</table>
<h2>Calls</h2>{''.join(call_blocks)}
</body></html>"""
    html_path = out / "report.html"
    html_path.write_text(page, encoding="utf-8")
    return json_path, html_path
