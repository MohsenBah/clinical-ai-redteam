# Rules of Engagement

Scope and constraints for MedSecLab red team activities against the clinical AI gateway lab environment.

---

## Authorization

| Item | Scope |
|------|-------|
| **Target** | `clinical-ai-gateway` lab deployment only |
| **Environment** | Local Docker Compose or designated lab VM |
| **Data** | Synthetic patient records only (`synthetic_patients.json`) |
| **Authorization** | Self-authorized lab — portfolio / research context |

**Not in scope:** Production systems, third-party APIs, real patient data, or internet-facing deployments without explicit written approval.

---

## Prohibited Activities

- Use of real PHI or identifiable patient data in queries or payloads
- Testing against production clinical AI systems
- Denial-of-service attacks beyond documented lab rate limits
- Credential stuffing or brute force against non-lab infrastructure
- Exfiltration of data outside the lab environment
- Social engineering of clinical staff or vendors

---

## Permitted Activities

- Prompt injection and jailbreak attempts (CAI-001, CAI-002, CAI-005, CAI-006)
- PHI probing with synthetic framing (CAI-003)
- Administrative query abuse testing (CAI-004)
- RAG ingestion of synthetic data and failed-ingest scenarios
- Correlation testing (repeated blocks → rule 100200)
- Audit log and SIEM analysis of all test traffic

---

## Data Handling

| Rule | Requirement |
|------|-------------|
| Synthetic only | All patient names/IDs are fabricated for the lab |
| Log retention | Lab logs may be used in reports and demo videos |
| Report redaction | No real credentials, API keys, or production hostnames in published artifacts |
| Payload storage | All attack strings documented in `payloads/` and attack catalog |

---

## Operational Constraints

- Run campaigns during lab maintenance windows when possible
- Document every attack in [attack-catalog.md](attack-catalog.md) before execution
- Record `request_id` and timestamp for each test for Wazuh/Grafana correlation
- Wait 2 seconds between rapid probes (demo scripts) to avoid overwhelming Ollama
- Do not disable gateway security controls to "make attacks succeed"

---

## Success Definition

A campaign is successful when:

1. Each executed CAI ID has documented gateway + detection outcomes
2. Results are recorded in [red-team-report-v1.md](red-team-report-v1.md)
3. Gaps (allowed attacks, missed rules) are explicitly listed as residual risk
4. No real PHI or production systems were involved

---

## Escalation

| Finding | Action |
|---------|--------|
| Gateway allows attack that should block | File gap in red team report → gateway blocklist PR |
| Wazuh misses blocked event | File gap → `clinical-ai-detections` rule PR |
| Both block and detect | Mark CAI ID as **Pass** in report |
| New attack variant | Assign next CAI ID; do not ad-hoc test without catalog entry |

---

## Related Documents

- [attack-catalog.md](attack-catalog.md) — CAI-001 through CAI-006
- [testing-methodology.md](testing-methodology.md) — execution and evidence collection
- [red-team-report-v1.md](red-team-report-v1.md) — findings deliverable
