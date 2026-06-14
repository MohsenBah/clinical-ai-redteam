# Garak Integration

[NVIDIA Garak](https://github.com/NVIDIA/garak) automated LLM vulnerability scanning, mapped to MedSecLab **CAI attack IDs**.

Garak extends automated probe coverage and cross-checks results against the manual campaign manifest.

## Prerequisites

```bash
pip install -r requirements-garak.txt

# Gateway running
cd ../clinical-ai-gateway && docker compose up -d
curl -s http://localhost:8000/health | jq
```

## Quick run

```bash
./scripts/run_garak.sh
```

Or directly (Garak **v0.11+** uses `model_type` / `model_name`):

```bash
python3 -m garak \
  --config garak/configs/clinical-ai-gateway.yaml \
  --model_type rest \
  --model_name clinical-ai-gateway \
  --generator_option_file garak/configs/rest-generator.json \
  --probes promptinject,encoding,dan,leakreplay
```

Verify config loaded:

```bash
python3 -m garak --config garak/configs/clinical-ai-gateway.yaml --list_config | grep model_type
```

## Configuration

| File | Purpose |
|------|---------|
| `configs/clinical-ai-gateway.yaml` | RestGenerator → `POST /query` |
| `cai-probe-map.json` | Garak probe → CAI ID expectations |

### Gateway integration

Garak sends probe text as the `query` field:

```json
{
  "query": "$INPUT",
  "user_id": "garak-scanner",
  "session_id": "garak-session"
}
```

- **Blocked injections** return HTTP **400** — config uses `skip_codes: [400]` so Garak treats gateway blocks as non-responses (expected for CAI-001/002).
- **Encoding bypass** (CAI-006) returns HTTP **200** — Garak detectors evaluate model output (documents the gap).

## Probe → CAI mapping

| Garak probe | CAI IDs | Manual expectation |
|-------------|---------|-------------------|
| `promptinject` | CAI-001, CAI-002 | Blocked |
| `dan` | CAI-001, CAI-005 | Blocked |
| `encoding` | CAI-006 | Allowed (gap) |
| `leakreplay` | CAI-002 | Blocked |

**Not covered by Garak** (use manual campaign): CAI-003 (PHI probing), CAI-004 (admin abuse).

## Compare to manual campaign

After a scan:

```bash
python3 scripts/compare_garak_campaign.py --report garak/reports/<latest>.report.jsonl
```

Checks Garak probe results against `cai-probe-map.json` and `campaign/campaign-manifest.json`.

## Reports

Scan output is saved under `garak/reports/` (gitignored). Commit mapping docs and configs; not raw scan artifacts unless needed for portfolio evidence.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_BASE_URL` | `http://localhost:8000` | Gateway base URL (override in yaml if needed) |
| `GARAK_GENERATIONS` | `3` | Generations per probe (lab-friendly; increase for production assessment) |
