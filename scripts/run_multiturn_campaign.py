#!/usr/bin/env python3
"""
Execute CAI-005 multi-turn scenarios against clinical-ai-gateway.

Works without PyRIT installed (stdlib orchestrator). Validates Wazuh rules
offline and writes reports/pyrit-<timestamp>.json.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from wazuh_offline import (
    CorrelationState,
    check_rules,
    evaluate_offline,
    gateway_block_reason,
)

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_FILE = ROOT / "pyrit" / "scenarios" / "cai-005-scenarios.json"
REPORTS_DIR = ROOT / "pyrit" / "reports"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def post_query(api_base: str, query: str, user_id: str, session_id: str) -> dict[str, Any]:
    body = {"query": query, "user_id": user_id, "session_id": session_id}
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        f"{api_base.rstrip('/')}/query",
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read().decode("utf-8")
            status = response.status
    except urllib.error.HTTPError as exc:
        status = exc.code
        raw = exc.read().decode("utf-8")

    try:
        parsed: dict[str, Any] | str = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        parsed = raw

    request_id = str(uuid.uuid4())
    if isinstance(parsed, dict):
        if "request_id" in parsed:
            request_id = str(parsed["request_id"])
        elif isinstance(parsed.get("detail"), dict) and "request_id" in parsed["detail"]:
            request_id = str(parsed["detail"]["request_id"])

    block_reason = gateway_block_reason(query)
    if block_reason:
        decision = "blocked"
        reason = block_reason
        category = "adversarial"
    elif status == 400:
        decision = "blocked"
        reason = "blocked_pattern:unknown"
        category = "adversarial"
    else:
        decision = "allowed"
        reason = "allowed"
        category = "unknown"

    audit_event = {
        "timestamp": utc_now(),
        "event_type": "query",
        "request_id": request_id,
        "user_id": user_id,
        "session_id": session_id,
        "query": query,
        "query_length": len(query),
        "decision": decision,
        "reason": reason,
        "query_category": category,
        "latency_ms": 2.0 if decision == "blocked" else 200.0,
    }

    return {
        "http_status": status,
        "response": parsed,
        "request_id": request_id,
        "audit_event": audit_event,
    }


def validate_turn(
    scenario_id: str,
    turn: dict[str, Any],
    result: dict[str, Any],
    correlation: CorrelationState,
    known_gap: bool,
) -> dict[str, Any]:
    audit = result["audit_event"]
    matched = sorted(evaluate_offline(audit, correlation))
    errors: list[str] = []

    if turn.get("expect_http") and result["http_status"] not in turn["expect_http"]:
        errors.append(
            f"http {result['http_status']} not in {turn['expect_http']}"
        )
    if turn.get("expect_decision") and audit.get("decision") != turn["expect_decision"]:
        errors.append(
            f"decision {audit.get('decision')!r} != {turn['expect_decision']!r}"
        )

    errors.extend(
        check_rules(
            f"{scenario_id}-turn{turn.get('turn', '?')}",
            set(matched),
            turn.get("expect_rules", []),
            turn.get("reject_rules", []),
        )
    )

    status = "pass" if not errors else "fail"
    if known_gap and not errors:
        status = "gap_documented"

    return {"matched_rules": matched, "errors": errors, "status": status}


def run_scenarios(args: argparse.Namespace) -> int:
    with Path(args.scenarios).open(encoding="utf-8") as handle:
        data = json.load(handle)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    campaign_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    correlation = CorrelationState()
    scenario_results: list[dict[str, Any]] = []
    failures = 0

    print(f"MedSecLab Multi-Turn Campaign — {campaign_id}")
    print(f"API: {args.api_base}")
    print(f"Scenarios: {args.scenarios}")
    print()

    for scenario in data.get("scenarios", []):
        sid = scenario["id"]
        print(f"=== {sid} (CAI-{scenario.get('cai_id', '005')}) ===")
        print(f"    {scenario.get('description', '')}")

        turn_results: list[dict[str, Any]] = []
        scenario_failures = 0

        for turn in scenario.get("turns", []):
            tnum = turn.get("turn", "?")
            print(f"  Turn {tnum}: {turn['query'][:72]}{'...' if len(turn['query']) > 72 else ''}")

            try:
                result = post_query(
                    args.api_base,
                    turn["query"],
                    scenario["user_id"],
                    scenario["session_id"],
                )
            except Exception as exc:
                validation = {"status": "error", "errors": [str(exc)], "matched_rules": []}
                turn_results.append({"turn": tnum, "error": str(exc), "validation": validation})
                scenario_failures += 1
                print(f"    ERROR: {exc}")
                continue

            validation = validate_turn(
                sid,
                turn,
                result,
                correlation,
                known_gap=bool(scenario.get("known_gap")),
            )
            turn_results.append(
                {
                    "turn": tnum,
                    "query": turn["query"],
                    "result": result,
                    "validation": validation,
                }
            )

            if validation["status"] == "fail":
                scenario_failures += 1
                for err in validation["errors"]:
                    print(f"    FAIL: {err}")
            else:
                print(
                    f"    {validation['status'].upper()}  HTTP {result['http_status']}  "
                    f"rules={validation.get('matched_rules') or 'none'}"
                )

            if args.sleep > 0:
                time.sleep(args.sleep)

        status = "pass" if scenario_failures == 0 else "fail"
        if scenario.get("known_gap") and scenario_failures == 0:
            status = "gap_documented"

        scenario_results.append(
            {
                "id": sid,
                "cai_id": scenario.get("cai_id"),
                "description": scenario.get("description"),
                "known_gap": scenario.get("known_gap", False),
                "gap_note": scenario.get("gap_note"),
                "user_id": scenario["user_id"],
                "session_id": scenario["session_id"],
                "status": status,
                "turns": turn_results,
            }
        )
        if scenario_failures:
            failures += scenario_failures
        print()

    report = {
        "campaign_id": campaign_id,
        "timestamp": utc_now(),
        "api_base": args.api_base,
        "orchestrator": "multiturn_campaign",
        "summary": {
            "scenarios": len(scenario_results),
            "failures": failures,
            "passed": sum(1 for s in scenario_results if s["status"] == "pass"),
            "gaps": sum(1 for s in scenario_results if s["status"] == "gap_documented"),
        },
        "scenarios": scenario_results,
    }

    report_path = REPORTS_DIR / f"pyrit-{campaign_id}.json"
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    print(f"Report: {report_path}")
    print(
        f"Summary: {report['summary']['passed']} passed, "
        f"{report['summary']['gaps']} gaps, {failures} turn failures"
    )
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run CAI-005 multi-turn scenarios")
    parser.add_argument("--api-base", default="http://localhost:8000")
    parser.add_argument("--scenarios", default=str(SCENARIOS_FILE))
    parser.add_argument("--sleep", type=float, default=2.0)
    args = parser.parse_args()
    return run_scenarios(args)


if __name__ == "__main__":
    sys.exit(main())
