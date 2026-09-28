"""Command line entry point: `callbench run ...`, `callbench serve-demo`."""
from __future__ import annotations

import argparse
import sys

from .metrics.scoring import summarize
from .report import compare_to_baseline, write_reports
from .runner import load_scenario, run_suite


def _progress(r) -> None:
    mark = "PASS" if r.passed else "FAIL"
    print(f"  [{mark}] {r.persona:<28} {r.language:<9} expected={r.expected.outcome:<15} "
          f"got={r.actual_outcome:<15} p95={r.latency_p95_ms:>6.0f}ms wer={r.wer:.0%}")


def cmd_run(args: argparse.Namespace) -> int:
    scenario = load_scenario(args.scenario)
    print(f"Scenario: {scenario.id} - {scenario.description}")
    results = run_suite(scenario, target=args.target, seed=args.seed,
                        use_llm_personas=args.llm_personas, progress=_progress)
    summary = summarize(results)
    delta = compare_to_baseline(summary, args.baseline) if args.baseline else None
    json_path, html_path = write_reports(results, args.out, title=f"callbench · {scenario.id}",
                                         baseline_delta=delta)
    print(f"\nPass rate {summary['pass_rate']:.0%} | p95 {summary['latency_p95_ms']:.0f} ms | "
          f"mean WER {summary['mean_wer']:.0%}")
    if delta:
        print("vs baseline:", ", ".join(f"{k} {v:+}" for k, v in delta.items()))
    print(f"Report: {html_path}\nJSON:   {json_path}")
    if args.fail_under is not None and summary["pass_rate"] < args.fail_under:
        print(f"FAILED gate: pass rate {summary['pass_rate']:.0%} < {args.fail_under:.0%}")
        return 1
    return 0


def cmd_serve_demo(args: argparse.Namespace) -> int:
    import uvicorn
    uvicorn.run("callbench.targets.demo_server:app", host=args.host, port=args.port)
    return 0


def cmd_web(args: argparse.Namespace) -> int:
    from .web.app import run
    run(args.host, args.port)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="callbench", description="Synthetic-caller tests for voice agents")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="run a scenario file")
    r.add_argument("scenario")
    r.add_argument("--target", default="demo", help="'demo' or base URL of an agent HTTP server")
    r.add_argument("--out", default="reports")
    r.add_argument("--seed", type=int, default=7)
    r.add_argument("--llm-personas", action="store_true", help="use an LLM to play callers (needs OPENAI_API_KEY)")
    r.add_argument("--baseline", help="previous results.json to compare against")
    r.add_argument("--fail-under", type=float, help="exit 1 if pass rate is below this (0-1), for CI")
    r.set_defaults(func=cmd_run)

    s = sub.add_parser("serve-demo", help="serve the demo agent over HTTP")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8080)
    s.set_defaults(func=cmd_serve_demo)

    w = sub.add_parser("web", help="open the web dashboard")
    w.add_argument("--host", default="127.0.0.1")
    w.add_argument("--port", type=int, default=int(__import__("os").getenv("PORT", "8000")))
    w.set_defaults(func=cmd_web)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
