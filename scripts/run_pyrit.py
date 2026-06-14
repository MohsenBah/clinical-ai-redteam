#!/usr/bin/env python3
"""
Optional PyRIT integration for CAI-005 multi-turn scenarios.

Falls back to scripts/run_multiturn_campaign.py when PyRIT is not installed.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "pyrit" / "scenarios" / "cai-005-scenarios.json"


def load_prompts() -> list[str]:
    with SCENARIOS.open(encoding="utf-8") as handle:
        data = json.load(handle)
    prompts: list[str] = []
    for scenario in data.get("scenarios", []):
        for turn in scenario.get("turns", []):
            prompts.append(turn["query"])
    return prompts


async def run_pyrit_orchestrator(api_base: str, prompts: list[str]) -> int:
    from pyrit.memory import DuckDBMemory
    from pyrit.orchestrator import PromptSendingOrchestrator
    from pyrit.prompt_target import HTTPTarget

    # Raw HTTP template — {PROMPT} replaced per request (PyRIT v0.11+)
    host = api_base.replace("http://", "").replace("https://", "")
    scheme = "https" if api_base.startswith("https") else "http"
    raw_request = (
        f"POST /query HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"Content-Type: application/json\r\n"
        f"Accept: application/json\r\n\r\n"
        f'{{"query": "{{PROMPT}}", "user_id": "pyrit-scanner", "session_id": "pyrit-session"}}'
    )

    def parse_gateway_response(response):
        """Extract answer or blocked detail from gateway JSON."""
        try:
            body = response.text if hasattr(response, "text") else str(response)
            data = json.loads(body)
            if isinstance(data, dict):
                if "answer" in data:
                    return data["answer"]
                if "detail" in data:
                    return json.dumps(data["detail"])
            return body
        except Exception:
            return str(response)

    memory = DuckDBMemory(db_path=str(ROOT / "pyrit" / "reports" / "pyrit-memory.duckdb"))
    target = HTTPTarget(
        http_request=raw_request,
        callback_function=parse_gateway_response,
        use_tls=scheme == "https",
    )

    orchestrator = PromptSendingOrchestrator(objective_target=target, memory=memory)
    await orchestrator.send_prompts_async(prompt_list=prompts[:10])  # lab subset
    print(f"PyRIT sent {min(len(prompts), 10)} prompts via HTTPTarget")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-base", default="http://localhost:8000")
    parser.add_argument("--fallback-only", action="store_true")
    args = parser.parse_args()

    if args.fallback_only:
        return subprocess.call(
            [sys.executable, str(ROOT / "scripts" / "run_multiturn_campaign.py"),
             "--api-base", args.api_base],
        )

    try:
        import pyrit  # noqa: F401
    except ImportError:
        print("PyRIT not installed — using stdlib multi-turn orchestrator")
        return subprocess.call(
            [sys.executable, str(ROOT / "scripts" / "run_multiturn_campaign.py"),
             "--api-base", args.api_base],
        )

    prompts = load_prompts()
    print("PyRIT available — running PromptSendingOrchestrator subset")
    try:
        return asyncio.run(run_pyrit_orchestrator(args.api_base, prompts))
    except Exception as exc:
        print(f"PyRIT run failed ({exc}) — falling back to stdlib orchestrator")
        return subprocess.call(
            [sys.executable, str(ROOT / "scripts" / "run_multiturn_campaign.py"),
             "--api-base", args.api_base],
        )


if __name__ == "__main__":
    sys.exit(main())
