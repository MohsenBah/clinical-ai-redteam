# PyRIT / Multi-Turn Orchestration

Multi-turn attack scenarios for **CAI-005**, mapped to Wazuh rule **100200** (repeated blocks) and escalation patterns.

## Design note

`clinical-ai-gateway` is **stateless** per request — `session_id` correlates audit/SIEM events but does not carry LLM memory between turns. Multi-turn tests here measure:

1. **Sequential attacks** in the same `user_id` / `session_id` (Wazuh correlation)
2. **Crescendo escalation** (benign → injection across turns)
3. **Stitched context** (simulated prior turns in one query string)

## Quick run

```bash
# Works without PyRIT
./scripts/run_pyrit.sh

# Or stdlib orchestrator directly
python3 scripts/run_multiturn_campaign.py
```

## Scenarios

| ID | Turns | Purpose |
|----|-------|---------|
| `cai-005-repeated-blocks` | 3 | Identical blocks → 100200 on 3rd |
| `cai-005-crescendo` | 3 | Benign → training framing → injection |
| `cai-005-stitched-context` | 1 | Stitched injection blocked (100100, 100102) |
| `cai-005-split-framing` | 2 | Benign framing then direct injection |

Definitions: `pyrit/scenarios/cai-005-scenarios.json`

## PyRIT integration

When `pyrit` is installed, `scripts/run_pyrit.py` uses `HTTPTarget` + `PromptSendingOrchestrator` against `POST /query`. On failure or missing install, falls back to `run_multiturn_campaign.py`.

```bash
pip install -r requirements-pyrit.txt
python3 scripts/run_pyrit.py --api-base http://localhost:8000
```

## Compare results

```bash
python3 scripts/compare_pyrit_campaign.py
```

Cross-references:

- `campaign/campaign-manifest.json` (CAI-005 repeated-block steps)
- `garak/cai-probe-map.json` (`dan` probe → CAI-005 partial)

## Reports

`pyrit/reports/pyrit-<timestamp>.json` (gitignored)
