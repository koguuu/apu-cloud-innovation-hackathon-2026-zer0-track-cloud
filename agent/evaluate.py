#!/usr/bin/env python3
"""Compare what the RULES decided with what GEMINI decided, on fixed test scenarios.

Runs each scenario in agent/scenarios/ through backend/app/analyzer.py: explain(), the same
function the live server uses, and prints rules vs Gemini vs final vs expected.

    python agent/evaluate.py                    # all scenarios
    python agent/evaluate.py ap_failure         # one or more by name
    python agent/evaluate.py --runs 3           # repeat to check Gemini is consistent
    python agent/evaluate.py --save             # also write agent/results/report.md

Needs GEMINI_API_KEY (in backend/.env or your environment). Without it, the script still runs but
shows the template fallback, which is not Gemini. Nothing here changes any backend state.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCEN_DIR = Path(__file__).resolve().parent / "scenarios"
REPORT = Path(__file__).resolve().parent / "results" / "report.md"
KNOWN = {"ap_hardware_failure", "congestion", "isp_uplink_outage", "iot_device_fault", "unknown"}


def load_env() -> None:
    """Minimal .env reader (real environment variables win). Never prints values."""
    for p in (ROOT / "backend" / ".env", ROOT / ".env"):
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def import_analyzer():
    sys.path.insert(0, str(ROOT / "backend"))
    from app import analyzer  # noqa: WPS433 (imported late on purpose)
    return analyzer


def load_scenarios(names: list[str] | None = None) -> list[dict]:
    out = []
    for f in sorted(SCEN_DIR.glob("*.json")):
        sc = json.loads(f.read_text(encoding="utf-8"))
        if not names or sc["name"] in names:
            out.append(sc)
    if names:
        missing = set(names) - {s["name"] for s in out}
        if missing:
            raise SystemExit(f"Unknown scenario(s): {', '.join(sorted(missing))}")
    return out


def _parse(raw):
    try:
        return json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
    except Exception:
        return {}


def run_scenario(sc: dict, analyzer) -> dict:
    """One call to the real explain(). A spy records Gemini's raw reply."""
    draft = analyzer.Draft(
        cause=sc["rule_cause"], location_id=sc["location_id"],
        affected_aps=list(sc.get("affected_aps", [])), affected_devices=list(sc.get("affected_devices", [])),
        evidence=copy.deepcopy(sc["evidence"]),
    )
    seen: dict = {}
    original = analyzer.llm.call_gemini

    def spy(prompt, *, json_mode=False):
        seen["raw"] = original(prompt, json_mode=json_mode)
        return seen["raw"]

    analyzer.llm.call_gemini = spy
    try:
        explanation, action = analyzer.explain(draft)
    finally:
        analyzer.llm.call_gemini = original

    data = _parse(seen.get("raw") or "")
    used_gemini = bool(data.get("explanation") and data.get("recommended_action"))
    gem_cause = data.get("root_cause") if data.get("root_cause") in KNOWN else None
    return {
        "name": sc["name"], "rules": sc["rule_cause"], "expected": sc["expected_cause"],
        "gemini": gem_cause, "confidence": data.get("confidence"), "final": draft.cause,
        "source": "gemini" if used_gemini else "template",
        "explanation": explanation, "action": action,
    }


def _verdict(r: dict) -> str:
    return "OK" if r["final"] == r["expected"] else "MISS"


def print_table(results: list[dict]) -> None:
    cols = [("scenario", 26, "name"), ("rules said", 19, "rules"), ("gemini said", 19, "gemini"),
            ("conf", 7, "confidence"), ("final", 19, "final"), ("expected", 19, "expected")]
    head = "  ".join(t.ljust(w) for t, w, _ in cols) + "  result"
    print(head)
    print("-" * len(head))
    for r in results:
        cells = []
        for _, w, k in cols:
            v = r[k] if r[k] is not None else "-"
            cells.append(str(v).ljust(w))
        note = "" if r["source"] == "gemini" else "  (template text: Gemini not used)"
        print("  ".join(cells) + "  " + _verdict(r) + note)


def summarise(results: list[dict]) -> list[str]:
    n = len(results)
    used = [r for r in results if r["source"] == "gemini"]
    rules_ok = sum(r["rules"] == r["expected"] for r in results)
    final_ok = sum(r["final"] == r["expected"] for r in results)
    gem_ok = sum(r["gemini"] == r["expected"] for r in used)
    overrides = sum(r["final"] != r["rules"] for r in results)
    gem_disagree = sum(r["gemini"] and r["gemini"] != r["rules"] for r in used)
    lines = [
        f"Runs: {n}   Gemini replies used: {len(used)}/{n}",
        f"Rules correct:            {rules_ok}/{n}",
        f"Gemini suggestion correct: {gem_ok}/{len(used)}" if used else "Gemini suggestion correct: n/a (no Gemini replies)",
        f"Final (after guard rails): {final_ok}/{n}",
        f"Gemini disagreed with rules: {gem_disagree}   Overrides applied: {overrides}",
    ]
    return lines


def write_report(results: list[dict], runs: int) -> None:
    REPORT.parent.mkdir(exist_ok=True)
    model = os.environ.get("GEMINI_MODEL", "backend default")
    lines = [f"# Agent evaluation report", "",
             f"Generated {datetime.now():%Y-%m-%d %H:%M} | model: {model} | runs per scenario: {runs}", "",
             "| scenario | rules said | gemini said | confidence | final | expected | result |",
             "|---|---|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['name']} | {r['rules']} | {r['gemini'] or '-'} | {r['confidence'] or '-'} | "
                     f"{r['final']} | {r['expected']} | {_verdict(r)} |")
    lines += ["", "## Summary", ""] + [f"- {s}" for s in summarise(results)]
    lines += ["", "## Text written for each ticket (last run)", ""]
    last = {r["name"]: r for r in results}
    for name, r in last.items():
        lines += [f"**{name}** ({r['source']})", f"- Explanation: {r['explanation']}", f"- Action: {r['action']}", ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport saved to {REPORT.relative_to(ROOT)}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*", help="scenario names (default: all)")
    ap.add_argument("--runs", type=int, default=1, help="repeat each scenario N times")
    ap.add_argument("--delay", type=float, default=1.0, help="seconds between Gemini calls (free-tier limits)")
    ap.add_argument("--save", action="store_true", help="write agent/results/report.md")
    args = ap.parse_args(argv)

    load_env()
    if not os.environ.get("GEMINI_API_KEY"):
        print("WARNING: GEMINI_API_KEY not set. You will see template text, NOT Gemini.\n")
    analyzer = import_analyzer()
    scenarios = load_scenarios(args.names)

    results = []
    for sc in scenarios:
        for _ in range(args.runs):
            results.append(run_scenario(sc, analyzer))
            time.sleep(args.delay if os.environ.get("GEMINI_API_KEY") else 0)

    print_table(results)
    print()
    for line in summarise(results):
        print(line)
    print()
    for r in results[:: max(args.runs, 1)]:
        print(f"[{r['name']}] ({r['source']})\n  {r['explanation']}\n  Action: {r['action']}\n")
    if args.save:
        write_report(results, args.runs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
