# Clinical AI Red Team

Adversarial testing and offensive security assessment for clinical LLM deployments.

**Build the attack methodology first — not Garak/PyRIT.** Curated attack IDs and a professional red team report are more valuable than hundreds of random payloads or a tool collection.

## Purpose

Systematically test clinical AI security end-to-end:

```
Attack (CAI-00x) → Gateway → Audit Log → Detection Rule → Grafana → Wazuh
```

Validate that gateway controls and SIEM detections work together, then document findings in **`docs/red-team-report-v1.md`**.

Part of the MedSecLab portfolio:

- [`clinical-ai-gateway`](https://github.com/MohsenBah/clinical-ai-gateway) — target system under test
- [`clinical-ai-detections`](https://github.com/MohsenBah/clinical-ai-detections) — Wazuh rules, Grafana, validation harness
- [`MedSecLab`](https://github.com/MohsenBah/MedSecLab) — portfolio coordination, threat model (Phase 5)

## Quick Start

```bash
# Terminal 1 — start gateway
cd ../clinical-ai-gateway && docker compose up

# Terminal 2 — automated campaign + validation (Phase 4.3)
cd clinical-ai-redteam
./scripts/run_campaign.sh
```

Manual demo (portfolio video style, fewer steps):

```bash
./scripts/run-demo.sh
```

## Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| **4.1** | Attack methodology (catalog, ROE, report v1) | ✅ Complete |
| **4.2** | Manual payloads per attack ID | ✅ Complete |
| **4.3** | Detection validation (`run_campaign.sh`) | ✅ Complete |
| **4.4** | Garak integration | ⏳ Next |
| **4.5** | PyRIT orchestration | ⏳ Later |

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
├── reports/                       # gitignored campaign output
└── scripts/
    ├── run_campaign.sh            # Automated campaign + validation
    ├── run_campaign.py
    ├── run-demo.sh                # Manual demo
    └── wazuh_offline.py           # Offline rule simulation
```

## Attack Catalog

| Attack ID | Category | Status |
|-----------|----------|--------|
| CAI-001 | Ignore previous instructions | Tested ✅ |
| CAI-002 | System prompt extraction | Tested ✅ |
| CAI-003 | PHI probing | Tested ✅ |
| CAI-004 | Administrative privilege abuse | Tested (gaps documented) |
| CAI-005 | Multi-turn injection | Tested ✅ |
| CAI-006 | Encoded injection | Tested (gap confirmed) |

Details: [docs/attack-catalog.md](docs/attack-catalog.md)

## Documentation

| Document | Description |
|----------|-------------|
| [attack-catalog.md](docs/attack-catalog.md) | CAI IDs, payloads, Wazuh mapping |
| [testing-methodology.md](docs/testing-methodology.md) | Evidence collection, pass/fail criteria |
| [rules-of-engagement.md](docs/rules-of-engagement.md) | Lab scope and constraints |
| [red-team-report-v1.md](docs/red-team-report-v1.md) | Findings and detection results |

## Future Tooling (Phase 4.4–4.5)

**Garak** and **PyRIT** are planned **after** manual campaigns prove the methodology.
