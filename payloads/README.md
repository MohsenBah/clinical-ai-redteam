# Payloads

Curated attack payloads mapped to CAI IDs in [docs/attack-catalog.md](../docs/attack-catalog.md).

Each file is a ready-to-send JSON body for `POST /query`.

```bash
curl -s -X POST "${API_BASE_URL}/query" \
  -H "Content-Type: application/json" \
  -d @payloads/prompt-injection/cai-001.json | jq
```

| File | CAI ID | Status |
|------|--------|--------|
| `prompt-injection/cai-001.json` | CAI-001 | Tested |
| `system-prompt-extraction/cai-002.json` | CAI-002 | Tested |
| `phi-probing/cai-003-ssn.json` | CAI-003 | Tested |
| `phi-probing/cai-003-address.json` | CAI-003 | Tested |
| `prompt-injection/cai-005-repeated.json` | CAI-005 | Tested (use 3×) |

Phase 4.2 will add CAI-004 and CAI-006 payloads.
