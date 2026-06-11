#!/usr/bin/env python3
"""
Execute red team campaign from campaign/campaign-manifest.json.

Posts each step to the gateway, collects API + audit evidence, validates Wazuh
rules offline, and writes reports/campaign-<timestamp>.json.
"""

from __future__ import annotations

import argparse
import json
import subprocess
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
    synthesize_audit_event,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "campaign" / "campaign-manifest.json"
REPORTS_DIR = ROOT / "reports"
DETECTIONS_CASES = ROOT.parent / "clinical-ai-detections" / "wazuh" / "tests" / "validation-cases.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def http_request(
    method: str,
    url: str,
    body: dict[str, Any] | None = None,
    timeout: float = 120.0,
) -> tuple[int, dict[str, Any] | str]:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            status = response.status
    except urllib.error.HTTPError as exc:
        status = exc.code
        raw = exc.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Request failed for {url}: {exc}") from exc

    try:
        parsed: dict[str, Any] | str = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        parsed = raw
    return status, parsed


def extract_request_id(status: int, response: dict[str, Any] | str) -> str:
    if not isinstance(response, dict):
        return str(uuid.uuid4())
    if "request_id" in response:
        return str(response["request_id"])
    detail = response.get("detail")
    if isinstance(detail, dict) and "request_id" in detail:
        return str(detail["request_id"])
    return str(uuid.uuid4())


def fetch_audit_from_docker(
    request_id: str,
    gateway_repo: Path,
    service: str,
) -> dict[str, Any] | None:
    compose_file = gateway_repo / "docker-compose.yml"
    if not compose_file.exists():
        return None

    cmd = [
        "docker",
        "compose",
        "-f",
        str(compose_file),
        "exec",
        "-T",
        service,
        "sh",
        "-c",
        f"grep -F '{request_id}' /app/logs/security.log | tail -1",
    ]
    try:
        proc = subprocess.run(
            cmd,
            cwd=gateway_repo,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None

    line = proc.stdout.strip()
    if not line:
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_payload(repo_root: Path, relative_path: str) -> dict[str, Any]:
    with (repo_root / relative_path).open(encoding="utf-8") as handle:
        return json.load(handle)


def cross_reference_validation_case(case_id: str | None, cases_path: Path) -> dict[str, Any] | None:
    if not case_id or not cases_path.exists():
        return None
    with cases_path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    for case in data.get("cases", []):
        if case.get("id") == case_id:
            return {
                "id": case_id,
                "expect_rules": case.get("expect_rules", []),
                "reject_rules": case.get("reject_rules", []),
            }
    return None


def run_step_query(
    api_base: str,
    payload: dict[str, Any],
    gateway_repo: Path,
    docker_service: str,
    use_docker_logs: bool,
) -> dict[str, Any]:
    timestamp = utc_now()
    status, response = http_request("POST", f"{api_base}/query", payload)
    request_id = extract_request_id(status, response)

    audit_event = None
    audit_source = "synthesized"
    if use_docker_logs:
        audit_event = fetch_audit_from_docker(request_id, gateway_repo, docker_service)
        if audit_event:
            audit_source = "docker_log"

    if audit_event is None:
        audit_event = synthesize_audit_event(
            payload,
            request_id=request_id,
            http_status=status,
            timestamp=timestamp,
        )

    return {
        "http_status": status,
        "response": response,
        "request_id": request_id,
        "audit_event": audit_event,
        "audit_source": audit_source,
    }


def validate_step(
    step: dict[str, Any],
    result: dict[str, Any],
    correlation: CorrelationState,
) -> dict[str, Any]:
    audit = result.get("audit_event") or {}
    matched = sorted(evaluate_offline(audit, correlation))

    errors: list[str] = []
    expect_http = step.get("expect_http", [])
    if expect_http and result.get("http_status") not in expect_http:
        errors.append(
            f"http status {result.get('http_status')} not in expected {expect_http}"
        )

    expect_decision = step.get("expect_decision")
    if expect_decision and audit.get("decision") != expect_decision:
        errors.append(
            f"decision {audit.get('decision')!r} != expected {expect_decision!r}"
        )

    errors.extend(
        check_rules(
            step["id"],
            set(matched),
            step.get("expect_rules", []),
            step.get("reject_rules", []),
        )
    )

    known_gap = bool(step.get("known_gap"))
    if known_gap and errors:
        # Documented gaps (CAI-004 abuse, CAI-006 encoding) pass when outcome matches gap intent
        gap_ok = (
            audit.get("decision") == step.get("expect_decision")
            and result.get("http_status") in step.get("expect_http", [200])
        )
        if gap_ok:
            errors = [
                e
                for e in errors
                if "missing expected rules" not in e and "matched rejected rules" not in e
            ]

    status = "pass" if not errors else "fail"
    if known_gap and status == "pass":
        status = "gap_documented"

    return {
        "matched_rules": matched,
        "errors": errors,
        "status": status,
        "known_gap": known_gap,
        "gap_note": step.get("gap_note"),
    }


def run_campaign(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    manifest = load_manifest(Path(args.manifest))
    api_base = args.api_base.rstrip("/")
    gateway_repo = Path(args.gateway_repo).resolve()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    campaign_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    correlation = CorrelationState()
    step_results: list[dict[str, Any]] = []
    failures = 0
    gaps = 0

    print(f"MedSecLab Red Team Campaign — {campaign_id}")
    print(f"API: {api_base}")
    print(f"Manifest: {args.manifest}")
    print()

    for step in manifest.get("steps", []):
        step_id = step["id"]
        cai = step.get("cai_id") or "-"
        print(f"[{step.get('phase', '?')}] {step_id} (CAI: {cai}) — {step.get('description', '')}")

        result: dict[str, Any]
        action = step.get("action")

        try:
            if action == "health":
                status, response = http_request("GET", f"{api_base}/health")
                result = {"http_status": status, "response": response}
            elif action == "clear_data":
                status, response = http_request("DELETE", f"{api_base}/data/clear")
                result = {"http_status": status, "response": response}
            elif action == "ingest":
                status, response = http_request(
                    "POST",
                    f"{api_base}/data/ingest",
                    step.get("ingest_body", {}),
                )
                result = {"http_status": status, "response": response}
            elif action == "query":
                payload = load_payload(repo_root, step["payload"])
                result = run_step_query(
                    api_base,
                    payload,
                    gateway_repo,
                    args.docker_service,
                    use_docker_logs=not args.no_docker_logs,
                )
            else:
                raise ValueError(f"Unknown action: {action}")
        except RuntimeError as exc:
            result = {"error": str(exc)}
            validation = {"status": "error", "errors": [str(exc)], "matched_rules": []}
            step_results.append(
                {
                    "id": step_id,
                    "cai_id": step.get("cai_id"),
                    "action": action,
                    "result": result,
                    "validation": validation,
                }
            )
            failures += 1
            print(f"  ERROR: {exc}")
            if not args.continue_on_error:
                break
            continue

        validation: dict[str, Any] = {"status": "skipped", "matched_rules": [], "errors": []}
        if action == "query" and "audit_event" in result:
            validation = validate_step(step, result, correlation)
            vcase = cross_reference_validation_case(
                step.get("validation_case"),
                Path(args.detections_cases),
            )
            if vcase:
                validation["validation_case"] = vcase

        record = {
            "id": step_id,
            "cai_id": step.get("cai_id"),
            "action": action,
            "description": step.get("description"),
            "known_gap": step.get("known_gap", False),
            "result": result,
            "validation": validation,
        }
        step_results.append(record)

        vstatus = validation.get("status", "skipped")
        if vstatus == "fail":
            failures += 1
            for err in validation.get("errors", []):
                print(f"  FAIL: {err}")
        elif vstatus == "gap_documented":
            gaps += 1
            print(f"  GAP: {step.get('gap_note', 'documented security gap')}")
            if validation.get("matched_rules"):
                print(f"  rules: {validation['matched_rules']}")
        elif vstatus == "pass":
            rules = validation.get("matched_rules", [])
            print(f"  PASS  HTTP {result.get('http_status')}  rules={rules or 'none'}")
        else:
            print(f"  OK    HTTP {result.get('http_status')}")

        if args.sleep > 0:
            time.sleep(args.sleep)

    report = {
        "campaign_id": campaign_id,
        "timestamp": utc_now(),
        "api_base": api_base,
        "summary": {
            "total_steps": len(step_results),
            "failures": failures,
            "documented_gaps": gaps,
            "passed": sum(
                1 for s in step_results if s.get("validation", {}).get("status") == "pass"
            ),
        },
        "steps": step_results,
    }

    report_path = REPORTS_DIR / f"campaign-{campaign_id}.json"
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    print()
    print(f"Report: {report_path}")
    print(
        f"Summary: {report['summary']['passed']} passed, "
        f"{gaps} documented gaps, {failures} failures "
        f"({report['summary']['total_steps']} steps)"
    )

    if failures:
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MedSecLab red team campaign")
    parser.add_argument("--api-base", default="http://localhost:8000")
    parser.add_argument("--manifest", default=str(MANIFEST))
    parser.add_argument("--repo-root", default=str(ROOT))
    parser.add_argument(
        "--gateway-repo",
        default=str(ROOT.parent / "clinical-ai-gateway"),
        help="Path to clinical-ai-gateway for docker log fetch",
    )
    parser.add_argument("--docker-service", default="gateway")
    parser.add_argument(
        "--no-docker-logs",
        action="store_true",
        help="Synthesize audit events instead of reading security.log",
    )
    parser.add_argument(
        "--detections-cases",
        default=str(DETECTIONS_CASES),
        help="clinical-ai-detections validation-cases.json for cross-reference",
    )
    parser.add_argument("--sleep", type=float, default=2.0, help="Seconds between steps")
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue campaign after a step error",
    )
    args = parser.parse_args()
    return run_campaign(args)


if __name__ == "__main__":
    sys.exit(main())
