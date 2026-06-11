#!/usr/bin/env bash
# MedSecLab Red Team — Phase 4.3 automated campaign
# Executes campaign-manifest.json, collects evidence, validates Wazuh rules offline.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_colors.sh
source "${SCRIPT_DIR}/_colors.sh"

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
GATEWAY_REPO="${GATEWAY_REPO:-$(cd "${SCRIPT_DIR}/../../clinical-ai-gateway" 2>/dev/null && pwd || echo "")}"
DEMO_SLEEP="${DEMO_SLEEP:-2}"

echo -e "${BLUE}MedSecLab Red Team — Automated Campaign (Phase 4.3)${NC}"
echo -e "${BLUE}API: ${API_BASE_URL}${NC}"
echo -e "${BLUE}Manifest: campaign/campaign-manifest.json${NC}"
echo

ARGS=(
  --api-base "${API_BASE_URL}"
  --sleep "${DEMO_SLEEP}"
  --continue-on-error
)

if [[ -n "${GATEWAY_REPO}" && -f "${GATEWAY_REPO}/docker-compose.yml" ]]; then
  ARGS+=(--gateway-repo "${GATEWAY_REPO}")
  echo -e "${BLUE}Audit logs: docker compose (${GATEWAY_REPO})${NC}"
else
  ARGS+=(--no-docker-logs)
  echo -e "${YELLOW}Gateway repo not found — synthesizing audit events${NC}"
fi

echo
exec python3 "${SCRIPT_DIR}/run_campaign.py" "${ARGS[@]}"
