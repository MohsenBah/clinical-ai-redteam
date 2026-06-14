#!/usr/bin/env bash
# MedSecLab — Phase 4.5 multi-turn / PyRIT orchestration (CAI-005)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# shellcheck source=_colors.sh
source "${SCRIPT_DIR}/_colors.sh"

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"

echo -e "${BLUE}MedSecLab Multi-Turn Campaign (Phase 4.5 — CAI-005)${NC}"
echo -e "${BLUE}API: ${API_BASE_URL}${NC}"
echo

if ! curl -sf "${API_BASE_URL}/health" >/dev/null; then
  echo -e "${YELLOW}Gateway not reachable at ${API_BASE_URL}${NC}"
  exit 1
fi

echo -e "${GREEN}[1/2] Run multi-turn scenarios${NC}"
if python3 -c "import pyrit" 2>/dev/null; then
  echo -e "${BLUE}PyRIT detected — attempting orchestrator (falls back on error)${NC}"
  python3 "${SCRIPT_DIR}/run_pyrit.py" --api-base "${API_BASE_URL}" || true
else
  echo -e "${BLUE}PyRIT not installed — using stdlib orchestrator${NC}"
  echo "  pip install -r requirements-pyrit.txt  # optional"
  python3 "${SCRIPT_DIR}/run_multiturn_campaign.py" --api-base "${API_BASE_URL}"
fi

echo
echo -e "${GREEN}[2/2] Compare to manual campaign + Garak${NC}"
python3 "${SCRIPT_DIR}/compare_pyrit_campaign.py"

echo
echo -e "${GREEN}Phase 4.5 complete.${NC}"
