# Clinical AI Red Team

Adversarial testing and offensive security assessment for clinical LLM deployments.

This repository contains attack frameworks, payload libraries, testing methodologies, and validation tools for systematically testing the security of clinical AI systems.

## Purpose

The goal is to identify vulnerabilities, validate detection effectiveness, and ensure robust security controls through:

- Automated adversarial testing campaigns
- Prompt injection and jailbreak assessment
- Data extraction and model reconnaissance testing
- Denial of service and resource exhaustion attacks
- Output manipulation and bias amplification testing
- Mitigation effectiveness validation

This repo is part of the MedSecLab portfolio architecture and complements:

- `clinical-ai-gateway` - Target system under test
- `clinical-ai-detections` - Detection rules and SIEM integration
- `MedSecLab` - Overall portfolio coordination

---

## Testing Framework

### Core Components

**Garak Integration**
- Automated LLM vulnerability scanner
- Clinical-specific probe configurations
- Custom vulnerability modules for healthcare AI

**PyRIT (Python Risk Identification Tool)**
- Red team orchestration framework
- Multi-turn conversation testing
- Automated attack sequencing

**Custom Attack Modules**
- Clinical-domain-specific attack vectors
- Healthcare regulatory bypass attempts
- PHI extraction techniques

---

## Attack Categories

### 1. Prompt Injection

**Direct Injection**
- Instruction override attempts
- Role-playing jailbreaks
- Context manipulation

**Indirect Injection**
- Encoded payloads (Base64, URL encoding)
- Multilingual attacks
- Unicode/emoji obfuscation

**Payload Locations**
- System prompt override
- Few-shot example poisoning
- RAG context injection

### 2. Jailbreaks

**DAN-Style Attacks**
- "Do Anything Now" variants
- Character roleplay bypasses
- Hypothetical scenario framing

**Encoding-Based**
- ROT13, Base64, hex encoding
- Leetspeak transformations
- Reverse text attacks

**Multi-Language**
- Non-English instruction sets
- Code-switching attacks
- Translation-based bypasses

### 3. Data Extraction

**System Prompt Leakage**
- Instruction reconstruction attacks
- Few-shot example extraction
- Safety guideline discovery

**Training Data Extraction**
- Membership inference
- Verbatim memorization attacks
- PHI reconstruction attempts

**Model Reconnaissance**
- Architecture fingerprinting
- Training data source identification
- Capability boundary testing

### 4. Denial of Service

**Resource Exhaustion**
- Token flooding attacks
- Infinite loop generation
- Memory exhaustion payloads

**Rate Limit Bypass**
- Distributed request patterns
- Credential rotation attacks
- Session manipulation

### 5. Output Manipulation

**Hallucination Induction**
- Contradictory context injection
- False premise establishment
- Authority impersonation

**Bias Amplification**
- Demographic targeting
- Stereotype reinforcement
- Clinical decision bias

---

## Repository Structure

```
clinical-ai-redteam/
├── README.md
├── docs/
│   ├── attack-catalog.md          # Comprehensive attack vector documentation
│   ├── testing-methodology.md     # Red team procedures and best practices
│   └── mitigation-validation.md   # Effectiveness testing framework
├── garak/
│   ├── configs/
│   │   └── clinical-ai-probes.yaml    # Clinical-specific Garak configuration
│   └── reports/                       # Generated vulnerability reports
├── pyrit/
│   ├── orchestrators/                 # Custom attack orchestrators
│   └── scorers/                       # Success/failure evaluators
├── attacks/
│   ├── prompt_injection/              # Injection attack modules
│   ├── jailbreaks/                    # Jailbreak techniques
│   ├── data_extraction/               # Extraction attack vectors
│   └── dos/                           # Denial of service attacks
├── payloads/
│   ├── injection/                     # Ready-to-use injection payloads
│   ├── jailbreak/                     # Jailbreak prompt libraries
│   └── extraction/                    # Data extraction templates
└── scripts/
    ├── run_campaign.sh                # Automated test campaign runner
    └── generate_report.py             # Report generation utility
```

---

## Integration with Detection Pipeline

### Inputs from Phase 3

**Detection Rules** (clinical-ai-detections)
- MITRE ATLAS-mapped rules (Phase 3.2A)
- Prompt injection patterns (Rule 100100-100102)
- Correlation rules (Rule 100200, 100300, 100400)

**Telemetry Schemas** (clinical-ai-gateway)
- Model performance metrics (Phase 3.1A)
- Query category classification
- Ingestion event logging

**Compliance Requirements** (Phase 3.3)
- HIPAA §164.312 controls
- OWASP LLM Top 10 risks
- NIST AI RMF functions

### Outputs to Detection Pipeline

**Attack Metrics**
- Success/failure rates per attack category
- False negative identification
- Detection latency measurements

**Mitigation Reports**
- Control effectiveness validation
- Gap analysis documentation
- Recommended rule enhancements

**Security Regression Tests**
- Automated test suites
- Continuous validation campaigns
- Pre-deployment security gates

### Feedback Loop

```
Attack Campaign → Detection Correlation → Rule Tuning
       ↑                                        ↓
Mitigation Gap ← Validation Report ← Attack Success
```

---

## Testing Methodology

### Campaign Execution

**1. Reconnaissance Phase**
- System fingerprinting
- Capability enumeration
- Safety boundary discovery

**2. Attack Phase**
- Payload deployment
- Multi-turn conversation testing
- Success criteria evaluation

**3. Analysis Phase**
- Attack success quantification
- Detection correlation analysis
- Mitigation gap identification

**4. Reporting Phase**
- Vulnerability documentation
- Risk scoring
- Remediation recommendations

### Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Attack Coverage | 50+ vectors | Attack catalog completeness |
| Automated Tests | 100+ cases | Test suite size |
| Mitigation Effectiveness | 90% | Blocked attack percentage |
| False Negative Rate | <5% | Missed detections |
| Test Execution Time | <2 hours | Campaign duration |

---

## Dependencies

### Required Repositories

| Repository | Purpose | Phase |
|------------|---------|-------|
| clinical-ai-gateway | Target system under test | Phase 1 |
| clinical-ai-detections | Detection rules for attack identification | Phase 2-3 |
| MedSecLab | Portfolio coordination | N/A |

### Infrastructure Requirements

- Mature gateway deployment with comprehensive logging
- Wazuh SIEM integration for attack detection correlation
- Grafana dashboards for attack metrics visualization
- Loki log aggregation for campaign analysis

### Tool Dependencies

- Garak (LLM vulnerability scanner)
- PyRIT (Red team orchestration)
- httpx (HTTP client for API testing)
- pytest (Test framework)

---

## Related Repositories

| Repository | Role |
|------------|------|
| `clinical-ai-gateway` | Primary target for adversarial testing |
| `clinical-ai-detections` | Detection rules and SIEM integration |
| `MedSecLab` | Overall portfolio architecture and documentation |

---

## Status

**Planned**

- ⏳ Repository structure created
- ⏳ Garak/PyRIT integration pending
- ⏳ Attack payload libraries pending
- ⏳ Automated testing framework pending
- ⏳ Documentation and methodology pending


