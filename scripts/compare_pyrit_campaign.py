#!/usr/bin/env python3
"""Compare multi-turn / PyRIT results to manual campaign and Garak expectations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "pyrit" / "scenarios" / "cai-005-scenarios.json"
MANIFEST = ROOT / "campaign" / "campaign-manifest.json"
REPORTS_DIR = ROOT / "pyrit" / "reports"


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def find_latest_report() -> Path | None:
    if not REPORTS_DIR.exists():
        return None
    files = sorted(REPORTS_DIR.glob("pyrit-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    scenarios = load_json(SCENARIOS)
    manifest = load_json(MANIFEST) if MANIFEST.exists() else {"steps": []}
    report_path = args.report or find_latest_report()

    print("=== PyRIT / Multi-Turn ↔ Manual Campaign Alignment ===\n")

    cai005_steps = [s for s in manifest.get("steps", []) if s.get("cai_id") == "CAI-005"]
    print(f"Manual campaign CAI-005 steps: {len(cai005_steps)} (repeated-block sequence)")
    print(f"Multi-turn scenarios: {len(scenarios.get('scenarios', []))}")
    print()

    for scenario in scenarios.get("scenarios", []):
        print(f"  {scenario['id']}: {len(scenario.get('turns', []))} turns — {scenario.get('description', '')}")

    print("\n--- Scenario coverage beyond manual campaign ---")
    manual_ids = {s["id"] for s in cai005_steps}
    for scenario in scenarios.get("scenarios", []):
        if scenario["id"] not in manual_ids and scenario["id"] != "cai-005-repeated-blocks":
            print(f"  + {scenario['id']}: {scenario.get('description', '')}")

    if report_path and report_path.exists():
        report = load_json(report_path)
        print(f"\n--- Report: {report_path.name} ---")
        print(f"Orchestrator: {report.get('orchestrator', 'unknown')}")
        summary = report.get("summary", {})
        print(
            f"Passed: {summary.get('passed', 0)}, "
            f"Gaps: {summary.get('gaps', 0)}, "
            f"Failures: {summary.get('failures', 0)}"
        )
        for scenario in report.get("scenarios", []):
            print(f"  {scenario['id']}: {scenario.get('status', '?')}")
    else:
        print("\nNo pyrit report found — run ./scripts/run_pyrit.sh first")

    print("\n--- Garak cross-reference ---")
    print("  Garak `dan` probe maps to CAI-001/005 (single-turn jailbreaks)")
    print("  Multi-turn scenarios here test sequential session correlation (100200)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
