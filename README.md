# Clinical AI Red Team

![Attacks](https://img.shields.io/badge/attack%20IDs-CAI--001--006-blue)
![Results](https://img.shields.io/badge/results-5%20detected%20%C2%B7%201%20partial%20%C2%B7%201%20remediated-brightgreen)
![Tools](https://img.shields.io/badge/tooling-manual%20%C2%B7%20Garak%20%C2%B7%20PyRIT-orange)

Adversarial testing and offensive security assessment for clinical LLM deployments. Part of the [MedSecLab](https://github.com/MohsenBah/MedSecLab) portfolio.

## Purpose

Systematically test clinical AI security end-to-end:

```
Attack (CAI-00x) → Gateway → Audit Log → Detection Rule → Grafana → Wazuh
```

Validate that gateway controls and SIEM detections work together, then document findings in **`docs/red-team-report-v1.md`**.

Part of the MedSecLab portfolio:

- [`clinical-ai-gateway`](https://github.com/MohsenBah/clinical-ai-gateway) — target system under test
- [`clinical-ai-detections`](https://github.com/MohsenBah/clinical-ai-detections) — Wazuh rules, Grafana, validation harness
- [`MedSecLab`](https://github.com/MohsenBah/MedSecLab) — portfolio coordination, threat model

## Quick Start

```bash
# Terminal 1 — start gateway
cd ../clinical-ai-gateway && docker compose up

# Terminal 2 — automated campaign + validation
cd clinical-ai-redteam
./scripts/run_campaign.sh

# Terminal 3 — Garak scan
pip install -r requirements-garak.txt
./scripts/run_garak.sh

# Terminal 4 — multi-turn / PyRIT
./scripts/run_pyrit.sh
```

Manual demo (fewer steps):

```bash
./scripts/run-demo.sh
```

## Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| **4.1** | Attack methodology (catalog, ROE, report v1) | ✅ Complete |
| **4.2** | Manual payloads per attack ID | ✅ Complete |
| **4.3** | Detection validation (`run_campaign.sh`) | ✅ Complete |
| **4.4** | Garak integration | ✅ Complete |
| **4.5** | PyRIT / multi-turn orchestration | ✅ Complete |
| **5** | STRIDE threat model (MedSecLab) | ✅ Complete |

## Repository Structure

```
clinical-ai-redteam/
├── README.md
├── campaign/
│   └── campaign-manifest.json     # Step expectations
├── docs/
│   ├── attack-catalog.md
│   ├── testing-methodology.md
│   ├── rules-of-engagement.md
│   └── red-team-report-v1.md
├── payloads/
│   ├── admin-abuse/
│   ├── baseline/
│   ├── phi-probing/
│   ├── prompt-injection/
│   └── system-prompt-extraction/
├── garak/
│   ├── configs/clinical-ai-gateway.yaml
│   ├── cai-probe-map.json
│   └── reports/                   # gitignored scan output
├── pyrit/
│   ├── scenarios/cai-005-scenarios.json
│   └── reports/                   # gitignored
├── requirements-garak.txt
├── requirements-pyrit.txt
└── scripts/
    ├── run_campaign.sh
    ├── run_garak.sh
    ├── run_pyrit.sh               # Multi-turn CAI-005
    ├── run_multiturn_campaign.py
    ├── compare_garak_campaign.py
    ├── compare_pyrit_campaign.py
    ├── run-demo.sh
    └── wazuh_offline.py
```

## Attack Catalog

| Attack ID | Category | Status |
|-----------|----------|--------|
| CAI-001 | Ignore previous instructions | Tested ✅ |
| CAI-002 | System prompt extraction | Tested ✅ |
| CAI-003 | PHI probing | Tested ✅ |
| CAI-004 | Administrative privilege abuse | Tested — found & remediated (100310) |
| CAI-005 | Multi-turn injection | Tested ✅ |
| CAI-006 | Encoded injection | Tested — found & remediated |

Details: [docs/attack-catalog.md](docs/attack-catalog.md)

## Documentation

| Document | Description |
|----------|-------------|
| [attack-catalog.md](docs/attack-catalog.md) | CAI IDs, payloads, Wazuh mapping |
| [testing-methodology.md](docs/testing-methodology.md) | Evidence collection, pass/fail criteria |
| [rules-of-engagement.md](docs/rules-of-engagement.md) | Lab scope and constraints |
| [red-team-report-v1.md](docs/red-team-report-v1.md) | Findings and detection results |

## Garak

```bash
pip install -r requirements-garak.txt
./scripts/run_garak.sh
```

Probe → CAI mapping: [garak/cai-probe-map.json](garak/cai-probe-map.json) · Details: [garak/README.md](garak/README.md)

## PyRIT / Multi-Turn

```bash
./scripts/run_pyrit.sh
```

CAI-005 scenarios: [pyrit/scenarios/cai-005-scenarios.json](pyrit/scenarios/cai-005-scenarios.json) · Details: [pyrit/README.md](pyrit/README.md)

Works without PyRIT installed (stdlib orchestrator). Install PyRIT with `pip install -r requirements-pyrit.txt` when needed.
