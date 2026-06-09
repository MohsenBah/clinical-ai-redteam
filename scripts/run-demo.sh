#!/usr/bin/env bash
# MedSecLab Red Team — Phase 4.1 demo campaign
# Maps each step to CAI IDs and expected Wazuh rules.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PAYLOAD_DIR="${REPO_ROOT}/payloads"
# shellcheck source=_colors.sh
source "${SCRIPT_DIR}/_colors.sh"

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
GATEWAY_DEMO="${GATEWAY_DEMO:-$(cd "${REPO_ROOT}/../clinical-ai-gateway/demo" 2>/dev/null && pwd || true)}"
SLEEP="${DEMO_SLEEP:-2}"

post_payload() {
  local label="$1"
  local file="$2"
  echo -e "${GREEN}${label}${NC}"
  curl -s -X POST "${API_BASE_URL}/query" \
    -H "Content-Type: application/json" \
    -d @"${file}" | jq || true
  sleep "${SLEEP}"
  echo
}

echo -e "${BLUE}MedSecLab Red Team — Demo Campaign (Phase 4.1)${NC}"
echo -e "${BLUE}API: ${API_BASE_URL}${NC}"
echo -e "${BLUE}Report: docs/red-team-report-v1.md${NC}"
echo

# --- Phase A: Baseline ---
echo -e "${BLUE}=== A1: Health check ===${NC}"
if [[ -n "${GATEWAY_DEMO}" && -x "${GATEWAY_DEMO}/01-health-check.sh" ]]; then
  # shellcheck source=/dev/null
  source "${GATEWAY_DEMO}/_colors.sh" 2>/dev/null || true
  "${GATEWAY_DEMO}/01-health-check.sh"
else
  curl -s "${API_BASE_URL}/health" | jq
  sleep "${SLEEP}"
fi
echo

echo -e "${BLUE}=== A2: Clear vector database ===${NC}"
curl -s -X DELETE "${API_BASE_URL}/data/clear" | jq || true
sleep "${SLEEP}"
echo

echo -e "${BLUE}=== A3: Failed ingestion (audit: status=failed) ===${NC}"
curl -s -X POST "${API_BASE_URL}/data/ingest" \
  -H "Content-Type: application/json" \
  -d '{"data_path": "/app/data/missing_file.csv"}' | jq || true
sleep "${SLEEP}"
echo

echo -e "${BLUE}=== A4: Successful ingestion (synthetic patients) ===${NC}"
curl -s -X POST "${API_BASE_URL}/data/ingest" \
  -H "Content-Type: application/json" \
  -d '{"data_path": "/app/data/synthetic_patients.json", "clear_existing": true}' | jq || true
sleep "${SLEEP}"
echo

echo -e "${BLUE}=== A5: Normal clinical query (no alert expected) ===${NC}"
if [[ -n "${GATEWAY_DEMO}" && -x "${GATEWAY_DEMO}/02-normal-query.sh" ]]; then
  "${GATEWAY_DEMO}/02-normal-query.sh"
else
  curl -s -X POST "${API_BASE_URL}/query" \
    -H "Content-Type: application/json" \
    -d '{"query": "What is the treatment plan for the patient with Type 2 Diabetes?", "user_id": "clinical-doc", "session_id": "ward-round-1"}' | jq
  sleep "${SLEEP}"
fi
echo

echo -e "${BLUE}=== A6: Administrative query baseline (CAI-004 prep) ===${NC}"
echo -e "${YELLOW}Benign admin query — abuse variants planned in CAI-004${NC}"
curl -s -X POST "${API_BASE_URL}/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the current system health status?", "user_id": "ops-user", "session_id": "ops-session"}' | jq
sleep "${SLEEP}"
echo

# --- Phase B: Adversarial ---
echo -e "${BLUE}=== B1: CAI-001 — Instruction override (Wazuh 100100, 100102) ===${NC}"
post_payload "[CAI-001] Blocked injection" "${PAYLOAD_DIR}/prompt-injection/cai-001.json"

echo -e "${BLUE}=== B2: CAI-002 — System prompt extraction (Wazuh 100100, 100101) ===${NC}"
post_payload "[CAI-002] System prompt extraction" "${PAYLOAD_DIR}/system-prompt-extraction/cai-002.json"

echo -e "${BLUE}=== B3: CAI-003 — PHI probing (Wazuh 100300, allowed query) ===${NC}"
post_payload "[CAI-003a] SSN / DOB probe" "${PAYLOAD_DIR}/phi-probing/cai-003-ssn.json"
post_payload "[CAI-003b] Address / MRN probe" "${PAYLOAD_DIR}/phi-probing/cai-003-address.json"

echo -e "${BLUE}=== B4: CAI-005 — Repeated probing (Wazuh 100200 on 3rd) ===${NC}"
echo -e "${BLUE}Expected: 100100 each; 100200 on probe 3/3 within 5 minutes${NC}"
for i in 1 2 3; do
  echo -e "${BLUE}  Probe ${i}/3${NC}"
  curl -s -X POST "${API_BASE_URL}/query" \
    -H "Content-Type: application/json" \
    -d @"${PAYLOAD_DIR}/prompt-injection/cai-005-repeated.json" | jq '.request_id, .detail // .answer' || true
  sleep "${SLEEP}"
done
echo

echo -e "${GREEN}Demo campaign complete.${NC}"
echo
echo -e "${BLUE}Evidence collection:${NC}"
echo "  1. Audit log:  docker compose exec gateway tail -30 /app/logs/security.log | jq -c ."
echo "  2. Wazuh:      validate with clinical-ai-detections/scripts/validate_rules.py"
echo "  3. Report:     update docs/red-team-report-v1.md if results differ"
echo
echo -e "${YELLOW}Planned (not in this demo): CAI-004 admin abuse, CAI-006 encoded injection${NC}"

sleep "${SLEEP}"
