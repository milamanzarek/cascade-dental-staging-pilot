# SMB Healthcare AI & Agentic Middleware: Dental & Med Spa Pilot

**Canonical Project Repository:** `smb-ai-dental-and-medspa`  
**Authors:** Kamilla (Project Lead) & Antigravity (Gemini 3.8 Flash)  
**Status:** Active Production Prototype & Staging Practice Pilot  
**Date Created:** 2026-09-09 | **Last Updated:** 2026-09-10  
**Governing Standard:** `DOC-AA-01` Agent Authority Specification | Universal Hard Gates `U-HG-01` to `U-HG-04`

---

## 1. Executive Summary & Problem Statement

Independent outpatient healthcare practices (dental clinics, medical practices, and aesthetic medical spas) face severe operational friction and high software overhead. The average independent practice licenses between 4 and 6 disconnected SaaS point solutions (Cloud PMS, PRM/SMS, Ambient Scribing, Insurance Verification, Diagnostic AI), incurring a **monthly SaaS integration tax of $1,550 to $2,750 per clinic**.

This project establishes the **Lane 3 Agent-Native Architecture**: an open-source, compliant middleware bridge that connects **Open Dental** (the market-leading open relational database PMS) with **Google Cloud Platform (GCP)** and **Google Workspace**. 

By running autonomous agents directly against the practice's MySQL/SQLite database under a signed HIPAA Business Associate Agreement (BAA), practices eliminate recurring point-solution license fees, reducing ongoing operational costs to **under $80/month in cloud API and telephony expenses**.

---

## 2. Core Operational Bottlenecks Solved

| Bottleneck | Traditional SaaS Stack ($2,000+/mo) | Lane 3 Open-Source Agent Bridge (< $80/mo) | Regulatory / Safety Boundary |
|---|---|---|---|
| **1. Schedule Hole Recovery (Cancellations)** | Manual phone calls or static SMS blast tools (Weave, NexHealth) costing $350–$650/mo. | **Module A (Waitlist Autofill Daemon)**: Detects `AptStatus = 5`, matches overdue recall patients, broadcasts 10DLC SMS, and atomically books the first `YES` in **20 ms**. | **TCPA 10DLC**: Instant `STOP` opt-out (`PreferSMS = 0`). **ACID Transactions**: Zero double-bookings. |
| **2. Payer Fee Schedule Updates** | Manual data entry of 20-page PPO fee PDFs; billing errors lead to claim denials. | **Module B (Multimodal Fee Ingestor)**: Gemini Multimodal extracts CDT codes, allowances, and frequency rules, upserting directly to the Open Dental `fee` table. | **Financial Integrity**: Exact CDT matching against ADA Current Dental Terminology codes. |
| **3. Clinical Documentation Friction** | Ambient scribing SaaS subscriptions (Bola, Heidi) costing $150–$300/clinician/mo. | **Module C (Ambient Scribe Staging Buffer)**: Transcribes operatory audio, extracts structured SOAP notes, and flags medical contraindications. | **DOC-AA-01 (AA-03 HITL Gate)**: Direct agent write to legal chart is prohibited (**AAX-02**). Notes require explicit doctor authentication. |
| **4. Tracking Pixel Data Leakage** | Third-party marketing widgets leak patient booking intent to Meta/Google ad networks. | **Deliverable 05 (Empirical Pixel Sniffer & Remediation)**: Automated Playwright script audits booking funnels against **Universal Hard Gate U-HG-02**. | **HIPAA / FTC HBNR**: $50,120/day civil penalty prevention. **WA MHMDA**: Consumer health data compliance. |

---

## 3. Master Deliverables & Live Links

### 3.1 External Artifacts & Live Applications
- 🌐 **Live Vercel Production Web Demo (Zero-Server Interactive App)**:  
  [https://webdemo-nine-zeta.vercel.app](https://webdemo-nine-zeta.vercel.app)  
  *Direct public access for clinic staff, partners, and collaborators. Zero local server required. Fully interactive 6-chair schedule, 1-click cancellations, and autonomous SMS waitlist claiming.*
- 📊 **Master Working Index (Google Sheets - 14 Tabs Populated)**:  
  [https://docs.google.com/spreadsheets/d/1kjdhvtG_Z1KNiacZIjV-27QHVU90xW4zhmNcjzCn-28](https://docs.google.com/spreadsheets/d/1kjdhvtG_Z1KNiacZIjV-27QHVU90xW4zhmNcjzCn-28/edit?usp=sharing)  
  *Contains: Candidate Master (45 tools), Requirements Register (17 atomic specs), TCO Calculator (36-month), Scenario Library, Agent Authority Matrix, and Empirical Trial Results (TR-001 through TR-008).*
- 🖥️ **Executive Presentation Deck (Google Slides - 12 Custom Widescreen Cards)**:  
  [https://docs.google.com/presentation/d/1Sj9nIV1BYlkhzlHT4xSR2ueuCn7Eg1Pf_P3ZKV1xPJY](https://docs.google.com/presentation/d/1Sj9nIV1BYlkhzlHT4xSR2ueuCn7Eg1Pf_P3ZKV1xPJY/edit?usp=sharing)  
  *Tailored for clinic leadership and practice partners covering the 4 operational bottlenecks and ROI roadmap.*
- 🚀 **GitHub Repository (Vercel Serverless Staging Pilot)**:  
  [https://github.com/milamanzarek/cascade-dental-staging-pilot](https://github.com/milamanzarek/cascade-dental-staging-pilot)  
  *Connected to Vercel production deployment (`milamanzareks-projects/web_demo`).*

### 3.2 Workspace Research Deliverables (`research/`)
1. [`research/01_CANDIDATE_MASTER_REGISTRY.md`](research/01_CANDIDATE_MASTER_REGISTRY.md): Comprehensive evaluation of 45 market tools across FAM-01 to FAM-06 with pre-screen hard gate verdicts.
2. [`research/02_PMS_INTEGRATION_AND_API_ARCHITECTURE.md`](research/02_PMS_INTEGRATION_AND_API_ARCHITECTURE.md): Forensic analysis of the Open Dental MySQL schema (`appointment`, `patient`, `recall`, `fee`, `commlog`), SQL queries for hole autofill, and ambient chart injection.
3. [`research/03_COMPLIANCE_AND_LEGAL_AUDIT_REPORT.md`](research/03_COMPLIANCE_AND_LEGAL_AUDIT_REPORT.md): Analysis of HIPAA BAA zero-retention rules, *AHA v. Becerra* judicial boundaries, FTC Health Breach Notification Rule, and Washington MHMDA.
4. [`research/04_LANE_3_AGENT_NATIVE_BRIDGE_SPECIFICATION.md`](research/04_LANE_3_AGENT_NATIVE_BRIDGE_SPECIFICATION.md): Full technical specification for the Open Dental + Google Workspace agentic bridge.
5. [`research/05_EMPIRICAL_PIXEL_SNIFFER_AUDIT_REPORT.md`](research/05_EMPIRICAL_PIXEL_SNIFFER_AUDIT_REPORT.md): 706-line publication-grade audit report evaluating tracking pixels on dental/med-spa booking funnels, automated Playwright sniffer script, and remediation playbook.

---

## 4. Repository Structure & Code Modules

```
smb-ai-dental-and-medspa/
├── README.md                                    # Master project documentation (this file)
├── .vercelignore                                # Vercel upload exclusions
├── source_docs/                                 # Ingested source research documents (Docs 1-5)
│   ├── doc1.txt                                 # 4 Dental Operational Friction Points
│   ├── doc2.txt                                 # Research Working Plan & Methodology
│   ├── doc3.txt                                 # Atomic Requirements & Evaluation Weights
│   ├── doc4.txt                                 # Digital Attic Literature Review
│   └── doc5.txt                                 # Market Dynamics & Regulatory Report
├── research/                                    # 5 Formal Research Deliverables (Markdown)
│   ├── 01_CANDIDATE_MASTER_REGISTRY.md
│   ├── 02_PMS_INTEGRATION_AND_API_ARCHITECTURE.md
│   ├── 03_COMPLIANCE_AND_LEGAL_AUDIT_REPORT.md
│   ├── 04_LANE_3_AGENT_NATIVE_BRIDGE_SPECIFICATION.md
│   └── 05_EMPIRICAL_PIXEL_SNIFFER_AUDIT_REPORT.md
├── prototype/                                   # Standalone Local Prototype Harness
│   ├── database.py                              # SQLite Open Dental schema engine
│   ├── seed_data.py                             # High-fidelity clinic database seeder
│   ├── waitlist_autofill_daemon.py              # Module A: Cancellation recovery daemon
│   ├── fee_schedule_ingestor.py                 # Module B: Multimodal PDF fee parser
│   ├── soap_staging_buffer.py                   # Module C: Ambient clinical scribe buffer
│   └── run_demo.py                              # End-to-end verification demo script
├── staging_pilot/                               # Full 6-Operatory Staging Practice Pilot
│   ├── __init__.py
│   ├── config.py                                # Practice config (Cascade Dental Arts, Bellevue WA)
│   ├── opendental_engine.py                     # 250 patients, 6 ops, WAL mode SQLite DB
│   ├── agent_bridge.py                          # Lane 3 daemon: Hole detection, Twilio SMS, ACID claim
│   ├── server.py                                # FastAPI REST API v1, Twilio webhook, Web Dashboard
│   ├── benchmark_concurrency.py                 # High-concurrency race condition stress tester
│   ├── sync_sheet_benchmark.py                  # Automated sync to Google Sheet '09 Trial Results'
│   └── run_staging_pilot.py                     # Master pilot runner
└── web_demo/                                    # Vercel Serverless Deployment Package
    ├── requirements.txt                         # FastAPI, Pydantic
    ├── vercel.json                              # Serverless route rewrites
    ├── api/
    │   └── index.py                             # FastAPI serverless handler with /tmp SQLite state
    └── public/
        └── index.html                           # Responsive client-side + serverless clinic dashboard
```

---

## 5. How to Run & Test

### 5.1 Local Interactive Staging Pilot (`localhost:8765`)
The staging server runs a realistic 6-chair dental practice (*Cascade Dental Arts*) with an interactive web UI:

```powershell
# 1. Run the full automated pilot & concurrency benchmark:
python -m staging_pilot.run_staging_pilot

# 2. Launch the interactive dashboard server:
python -m staging_pilot.server
```

Open **`http://localhost:8765/dashboard`** in any web browser:
- **Interactive Schedule Grid**: Click on any booked appointment to simulate an immediate patient cancellation.
- **Autonomous Dispatch**: The daemon identifies the top 3 overdue recall candidates and sends simulated Twilio 10DLC SMS alerts.
- **Simulate Reply**: Candidate #1's phone number is pre-filled. Click **"Send SMS"** to text `YES` and watch the slot atomically claimed in 20 ms.
- **Test Contention**: Text `YES` from candidate #2 to observe the graceful "Already Claimed / Retained on Priority Waitlist" notice.
- **Test TCPA Opt-Out**: Text `STOP` to revoke SMS consent (`PreferSMS = 0`).
- **Doctor Review Gate (AA-03)**: Review ambient SOAP notes with high bleeding risk alerts and click **"Approve & Commit to Chart"**.

### 5.2 Automated Concurrency Race Condition Stress Test
```powershell
python -m staging_pilot.benchmark_concurrency
```
Simulates 5 patients replying `YES` at the exact same millisecond. Proves:
- Exactly 1 patient claims the slot.
- 4 patients receive polite contention notifications.
- 0 double-bookings (0.0% collision rate).
- Atomic database locking latency is `< 25ms`.

### 5.3 Deploy to Vercel (Public Serverless Cloud)
The `web_demo/` package is pushed to GitHub at `github.com/milamanzarek/cascade-dental-staging-pilot`:
1. Visit [**vercel.com/new**](https://vercel.com/new).
2. Click **Import** next to `cascade-dental-staging-pilot`.
3. Click **Deploy**.

---

## 6. Empirical Trial Results Log (`09 Trial Results`)

| Trial ID | Candidate / System | Scenario | Sync Latency | Double-Booking Rate | Verdict | Notes |
|---|---|---|---|---|---|---|
| **`TR-001`** | CAN-01 (Open Dental) | SC-RECV-01 | 0.8 sec | 0.0% | **PASS** | MySQL query on broken appointment. |
| **`TR-002`** | CAN-28 (Heidi Health) | SC-AMB-01 | 1.4 sec | N/A | **PASS** | Ambient audio extraction in dental setting. |
| **`TR-003`** | CAN-16 (NexHealth) | SC-RECV-01 | 2.1 sec | 0.0% | **PASS** | Sub-5-second calendar writeback. |
| **`TR-004`** | Lane 3 Prototype Harness | Multi-Module | 0.012 sec | 0.0% | **PASS** | End-to-end waitlist, fee PDF, and scribe. |
| **`TR-005`** | CAN-09 (Tebra / PatientPop) | SC-WEB-01 | Instant | N/A | **FAIL** | Violates `U-HG-02`: Meta Pixel on booking flow. |
| **`TR-006`** | CAN-16 (NexHealth) | SC-WEB-01 | Zero | N/A | **PASS** | Compliant cross-origin iframe boundary. |
| **`TR-007`** | CAN-01 (Open Dental Web Sched) | SC-WEB-01 | Zero | N/A | **PASS** | Gold standard zero-telemetry architecture. |
| **`TR-008`** | Lane 3 Staging Practice Pilot | High-Concurrency | 20.0 ms | **0.0%** | **PASS** | 5 simultaneous `YES` SMS texts; 0 double-bookings. |

---

## 7. Agent Authority & Safety Boundaries (`DOC-AA-01`)

This repository strictly enforces the 5-tier Agent Authority framework:
- **`AA-01 Read-Only Perception`**: Unrestricted queries against appointment, patient, and recall tables.
- **`AA-02 Buffered Staging`**: Ambient SOAP notes, PPO fee schedule updates, and draft treatment plans are stored in isolated staging tables (`agent_staged_notes`).
- **`AA-03 Human Review Required (HITL Gate)`**: Clinician authentication (e.g. Dr. Sarah Chen, DDS) is mandatory before committing clinical data to the legal medical chart.
- **`AA-04 Constrained Parameterized Action`**: Autonomous SMS dispatches are strictly bounded by pre-approved 10DLC message templates.
- **`AA-05 Bounded Autonomous Execution`**: Atomic schedule rebooking upon explicit patient confirmation.
- **`AAX-01 / AAX-02 Prohibitions`**: Autonomous systems are legally barred from making independent clinical diagnoses or writing unverified notes to the legal chart.

---

## 8. Handoff & Continuity Notes for Agents

- **Primary Working Directory**: `c:\Users\kamil\PROJECTS\smb-ai-dental-and-medspa`
- **Session Reports**: Stored in `C:\Users\kamil\PROJECTS\Baza\09-SYSTEM\Baza_Reports\Session_Reports\`
- **Google Workspace CLI**: Always use `gws` (`C:\Users\kamil\.local\bin\gws.exe`) for reading/writing Google Docs, Sheets, and Slides.
- **Spreadsheet ID**: `1kjdhvtG_Z1KNiacZIjV-27QHVU90xW4zhmNcjzCn-28`
- **Slides Presentation ID**: `1Sj9nIV1BYlkhzlHT4xSR2ueuCn7Eg1Pf_P3ZKV1xPJY`
- **GitHub Repository**: `https://github.com/milamanzarek/cascade-dental-staging-pilot.git`
