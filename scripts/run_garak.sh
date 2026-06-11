#!/usr/bin/env bash
# MedSecLab — Garak scan against clinical-ai-gateway (Phase 4.4)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# shellcheck source=_colors.sh
source "${SCRIPT_DIR}/_colors.sh"

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
GARAK_CONFIG="${GARAK_CONFIG:-${REPO_ROOT}/garak/configs/clinical-ai-gateway.yaml}"
GARAK_GENERATOR_JSON="${GARAK_GENERATOR_JSON:-${REPO_ROOT}/garak/configs/rest-generator.json}"
REPORTS_DIR="${REPO_ROOT}/garak/reports"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
REPORT_PREFIX="${REPORTS_DIR}/garak-${TIMESTAMP}"
GARAK_PROBES="${GARAK_PROBES:-promptinject,encoding,dan,leakreplay}"

mkdir -p "${REPORTS_DIR}"

echo -e "${BLUE}MedSecLab Garak Scan (Phase 4.4)${NC}"
echo -e "${BLUE}Gateway: ${API_BASE_URL}${NC}"
echo -e "${BLUE}Config:  ${GARAK_CONFIG}${NC}"
echo -e "${BLUE}Garak:   requires v0.11+ (model_type / model_name)${NC}"
echo

if ! python3 -c "import garak" 2>/dev/null; then
  echo -e "${YELLOW}Garak not installed.${NC}"
  echo "  pip install -r requirements-garak.txt"
  exit 1
fi

echo -e "${GREEN}[1/4] Verify Garak config loads${NC}"
if ! python3 -m garak --config "${GARAK_CONFIG}" --list_config 2>&1 | grep -q "model_type"; then
  echo -e "${YELLOW}Config may not have loaded model_type — using CLI flags as fallback${NC}"
fi
python3 -m garak --config "${GARAK_CONFIG}" --list_config 2>&1 | grep -E "model_type|model_name|probe_spec" || true
echo

echo -e "${GREEN}[2/4] Health check${NC}"
if ! curl -sf "${API_BASE_URL}/health" >/dev/null; then
  echo -e "${YELLOW}Gateway not reachable at ${API_BASE_URL}${NC}"
  echo "  cd ../clinical-ai-gateway && docker compose up -d"
  exit 1
fi
curl -s "${API_BASE_URL}/health" | jq .
echo

echo -e "${GREEN}[3/4] Garak scan${NC}"
echo -e "${BLUE}Probes: ${GARAK_PROBES}${NC}"
echo -e "${BLUE}Reports: ${REPORT_PREFIX}.*${NC}"
echo

# Garak v0.11 uses --model_type / --model_name (not target_type)
# CLI flags reinforce yaml config; -G provides RestGenerator body
set +e
python3 -m garak \
  --config "${GARAK_CONFIG}" \
  --model_type rest \
  --model_name clinical-ai-gateway \
  --generator_option_file "${GARAK_GENERATOR_JSON}" \
  --probes "${GARAK_PROBES}" \
  --report_prefix "${REPORT_PREFIX}" \
  --skip_unknown \
  2>&1 | tee "${REPORT_PREFIX}.log"
GARAK_EXIT=$?
set -e

if [[ ${GARAK_EXIT} -ne 0 ]]; then
  echo -e "${YELLOW}Garak exited ${GARAK_EXIT} — check ${REPORT_PREFIX}.log${NC}"
  echo -e "${BLUE}Tip: garak.log in ~/.local/share/garak/ or project cwd may have detector errors${NC}"
fi

echo
echo -e "${GREEN}[4/4] Compare to manual campaign${NC}"
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
  echo -e "${YELLOW}No .report.jsonl found — check log for 'No detectors' or probe load errors${NC}"
fi

echo
echo -e "${GREEN}Garak phase complete.${NC}"
echo -e "${BLUE}Map: garak/cai-probe-map.json | Manual: ./scripts/run_campaign.sh${NC}"

exit "${GARAK_EXIT}"
