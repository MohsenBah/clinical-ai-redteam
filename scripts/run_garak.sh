#!/usr/bin/env bash
# MedSecLab — Garak scan against clinical-ai-gateway (Phase 4.4)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# shellcheck source=_colors.sh
source "${SCRIPT_DIR}/_colors.sh"

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
GARAK_CONFIG="${GARAK_CONFIG:-${REPO_ROOT}/garak/configs/clinical-ai-gateway.yaml}"
REPORTS_DIR="${REPO_ROOT}/garak/reports"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
REPORT_PREFIX="${REPORTS_DIR}/garak-${TIMESTAMP}"

mkdir -p "${REPORTS_DIR}"

echo -e "${BLUE}MedSecLab Garak Scan (Phase 4.4)${NC}"
echo -e "${BLUE}Gateway: ${API_BASE_URL}${NC}"
echo -e "${BLUE}Config:  ${GARAK_CONFIG}${NC}"
echo

if ! python3 -c "import garak" 2>/dev/null; then
  echo -e "${YELLOW}Garak not installed.${NC}"
  echo "  pip install -r requirements-garak.txt"
  exit 1
fi

echo -e "${GREEN}[1/3] Health check${NC}"
if ! curl -sf "${API_BASE_URL}/health" >/dev/null; then
  echo -e "${YELLOW}Gateway not reachable at ${API_BASE_URL}${NC}"
  echo "  cd ../clinical-ai-gateway && docker compose up -d"
  exit 1
fi
curl -s "${API_BASE_URL}/health" | jq .
echo

echo -e "${GREEN}[2/3] Garak scan (promptinject, encoding, dan, leakreplay)${NC}"
echo -e "${BLUE}Reports: ${REPORT_PREFIX}.*${NC}"
echo

# Garak writes to ~/.local/share/garak by default; also pass report prefix when supported
python3 -m garak \
  --config "${GARAK_CONFIG}" \
  --report_prefix "${REPORT_PREFIX}" \
  2>&1 | tee "${REPORT_PREFIX}.log" || {
    echo -e "${YELLOW}Garak exited non-zero — check ${REPORT_PREFIX}.log${NC}"
  }

echo
echo -e "${GREEN}[3/3] Compare to manual campaign${NC}"
LATEST_REPORT=""
if [[ -f "${REPORT_PREFIX}.report.jsonl" ]]; then
  LATEST_REPORT="${REPORT_PREFIX}.report.jsonl"
else
  LATEST_REPORT="$(find "${REPORTS_DIR}" -name '*.report.jsonl' -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2- || true)"
fi

if [[ -n "${LATEST_REPORT}" && -f "${LATEST_REPORT}" ]]; then
  python3 "${SCRIPT_DIR}/compare_garak_campaign.py" --report "${LATEST_REPORT}"
else
  python3 "${SCRIPT_DIR}/compare_garak_campaign.py"
  echo -e "${YELLOW}No .report.jsonl found — alignment expectations only.${NC}"
fi

echo
echo -e "${GREEN}Garak phase complete.${NC}"
echo -e "${BLUE}Map: garak/cai-probe-map.json | Manual: ./scripts/run_campaign.sh${NC}"
