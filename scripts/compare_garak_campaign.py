#!/usr/bin/env python3
"""
Compare Garak scan output to manual campaign expectations (CAI IDs).

Reads:
  - garak/cai-probe-map.json
  - campaign/campaign-manifest.json (known_gap steps)
  - Garak .report.jsonl (optional)

Usage:
  python3 scripts/compare_garak_campaign.py
  python3 scripts/compare_garak_campaign.py --report garak/reports/scan.report.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP_FILE = ROOT / "garak" / "cai-probe-map.json"
MANIFEST = ROOT / "campaign" / "campaign-manifest.json"
REPORTS_DIR = ROOT / "garak" / "reports"


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def find_latest_report(directory: Path) -> Path | None:
    if not directory.exists():
        return None
    candidates = sorted(
        directory.glob("*.report.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def parse_garak_report(path: Path) -> dict[str, dict[str, int]]:
    """Summarize Garak JSONL by probe module and detector status."""
    by_probe: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            probe = (
                entry.get("probe")
                or entry.get("probe_classname")
                or entry.get("entry_type")
                or "unknown"
            )
            if isinstance(probe, str) and "." in probe:
                probe = probe.split(".")[-1]

            status = (
                entry.get("status")
                or entry.get("detector_result")
                or entry.get("result")
                or "logged"
            )
            by_probe[str(probe).lower()][str(status).lower()] += 1

    return {k: dict(v) for k, v in by_probe.items()}


def manifest_gaps(manifest: dict) -> list[dict]:
    return [
        {
            "id": step["id"],
            "cai_id": step.get("cai_id"),
            "gap_note": step.get("gap_note"),
        }
        for step in manifest.get("steps", [])
        if step.get("known_gap")
    ]


def print_alignment(map_data: dict, manifest: dict, garak_summary: dict[str, dict[str, int]] | None) -> int:
    issues = 0

    print("=== Garak ↔ CAI ↔ Manual Campaign Alignment ===\n")

    for mapping in map_data.get("mappings", []):
        probes = mapping.get("garak_probes", [])
        cai_ids = mapping.get("cai_ids", [])
        expectation = mapping.get("manual_campaign_expectation")
        known_gap = mapping.get("known_gap", False)

        print(f"Probes: {', '.join(probes)} → CAI {', '.join(cai_ids)}")
        print(f"  Manual expectation: {expectation}")
        if known_gap:
            print(f"  Known gap: {mapping.get('notes', '')}")

        if garak_summary:
            for probe in probes:
                stats = garak_summary.get(probe.lower(), {})
                if stats:
                    print(f"  Garak stats ({probe}): {stats}")
                else:
                    print(f"  Garak stats ({probe}): no entries in report")
        print()

    print("--- Manual campaign known gaps ---")
    for gap in manifest_gaps(manifest):
        print(f"  {gap['cai_id']} ({gap['id']}): {gap.get('gap_note', 'gap')}")

    print("\n--- Not in Garak (manual only) ---")
    for item in map_data.get("not_in_garak", []):
        print(f"  {item['cai_id']}: {item['reason']}")

    if garak_summary is None:
        print("\nNo Garak report provided — showing expected alignment only.")
        print("Run ./scripts/run_garak.sh to generate a report.")
        return 0

    # Basic alignment checks
    print("\n--- Alignment checks ---")
    encoding_stats = garak_summary.get("encoding", {})
    if encoding_stats:
        print("  CAI-006: Garak encoding probe ran — expect gateway blocks (encoding bypass remediated)")
    else:
        print("  WARN: No encoding probe data in report")
        issues += 1

    prompt_stats = garak_summary.get("promptinject", {})
    if prompt_stats:
        print("  CAI-001/002: Garak promptinject ran — gateway should block many (HTTP 400)")
    else:
        print("  WARN: No promptinject probe data in report")
        issues += 1

    if issues:
        print(f"\nAlignment review: {issues} warning(s)")
        return 0

    print("\nAlignment review: OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare Garak results to CAI campaign")
    parser.add_argument("--report", type=Path, help="Path to Garak .report.jsonl")
    parser.add_argument("--map", type=Path, default=MAP_FILE)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    args = parser.parse_args()

    if not args.map.exists():
        print(f"Map file not found: {args.map}", file=sys.stderr)
        return 1

    map_data = load_json(args.map)
    manifest = load_json(args.manifest) if args.manifest.exists() else {"steps": []}

    report_path = args.report or find_latest_report(REPORTS_DIR)
    garak_summary = None
    if report_path and report_path.exists():
        print(f"Report: {report_path}\n")
        garak_summary = parse_garak_report(report_path)
    else:
        print("No Garak report found.\n")

    return print_alignment(map_data, manifest, garak_summary)


if __name__ == "__main__":
    sys.exit(main())
