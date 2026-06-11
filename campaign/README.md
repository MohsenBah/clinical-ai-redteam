# Campaign Manifest

`campaign-manifest.json` defines the full red team campaign executed by `scripts/run_campaign.sh`.

Each step specifies:

- **payload** or **ingest/health** action
- **expect_http** / **expect_decision** — gateway outcome
- **expect_rules** / **reject_rules** — offline Wazuh validation
- **validation_case** — cross-reference to `clinical-ai-detections/wazuh/tests/validation-cases.json`
- **known_gap** — documented security gap (passes when gap behavior is confirmed)

## Run

```bash
# Gateway must be running
cd ../clinical-ai-gateway && docker compose up -d

cd clinical-ai-redteam
./scripts/run_campaign.sh
```

Reports are written to `reports/campaign-<timestamp>.json` (gitignored).

## Offline mode

If the gateway repo is not available for docker log fetch, the runner synthesizes audit events from gateway blocklist logic (`scripts/wazuh_offline.py`).

```bash
python3 scripts/run_campaign.py --no-docker-logs --api-base http://localhost:8000
```
