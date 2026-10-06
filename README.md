# JEEVDESK (ஜீவ்டெஸ்க்)
## AI-Driven Multilingual Voice Assistant for Livelihood Mapping & NSQF-Aligned Skilling Recommendations
### Under PM-AJAY Grant-in-Aid (Problem Statement ID: 26097 | MoSJE)

---

## 1. System Overview
**JEEVDESK** is an empathetic, voice-first livelihood assistant tailored for Scheduled Caste (SC) beneficiaries under the Grant-in-Aid (GIA) component of the **Pradhan Mantri Anusuchit Jaati Abhyuday Yojana (PM-AJAY)**. It addresses low digital literacy, language barriers, and fragmented referral systems by providing natural speech interaction in regional languages (Tamil, Hindi, English), constructing structured beneficiary profiles, and generating explainable National Skills Qualification Framework (NSQF) training and market pathways.

---

## 2. Implemented Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        JEEVDESK System Stack                          │
└────────────────────────────────────────────────────────────────────────┘
                                 │
           ┌─────────────────────┴─────────────────────┐
           ▼                                           ▼
┌─────────────────────────┐               ┌─────────────────────────┐
│     Beneficiary &       │               │   Field Facilitator &   │
│  Assisted Voice Client  │               │   M&E Web Portal        │
│  (Tamil / Hindi / Eng)  │               │   (Responsive HTML5)    │
└──────────┬──────────────┘               └────────────┬────────────┘
           │                                           │
           └─────────────────────┬─────────────────────┘
                                 │ REST / WebRTC / WebSpeech
                                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   JEEVDESK FastAPI Backend Service                     │
│                                                                        │
│ • Voice Dialogue Manager (Repair, Silence, Repetition & Escalation)    │
│ • Structured Profile Extractor (Provenance & Confidence Tracking)      │
│ • Explainable NSQF Recommendation Engine (Multi-criteria Scoring)      │
│ • Case Referral & Post-Skilling Lifecycle Workflow                     │
│ • Audit Logging & Data Minimization Governance Engine                  │
└────────────────────────────────┬───────────────────────────────────────┘
                                 │
           ┌─────────────────────┴─────────────────────┐
           ▼                                           ▼
┌──────────────────────────┐               ┌──────────────────────────┐
│   Curated NSQF Catalog   │               │ Local Opportunity Store  │
│  (Agriculture, FoodTech, │               │ (FPOs, Cluster Grants,   │
│  Apparel, Solar, Auto)   │               │ MSMEs, Verified Jobs)    │
└──────────────────────────┘               └──────────────────────────┘
```

---

## 3. Directory Layout
```
d:\PROJECTS\SIH2026\jeevdesk\
├── backend\
│   └── app\
│       ├── main.py                  # FastAPI Application Entrypoint & Endpoints
│       ├── models\
│       │   └── schemas.py           # Pydantic Schemas (Profile, Catalog, Rec, Case)
│       └── services\
│           ├── recommender.py       # Multi-criteria NSQF Matching & XAI Breakdown
│           └── voice_pipeline.py    # Multilingual Conversational Dialogue Manager
├── data\
│   ├── qualifications_catalog.json  # 8 NSQF PM-AJAY Aligned Courses
│   └── opportunities_catalog.json   # 6 Verified District Opportunities & Grants
├── frontend\
│   └── index.html                   # Integrated Voice Assistant & M&E Portal UI
├── docs\
│   └── ARCHITECTURE.md              # Technical and Governance Documentation
└── run_server.py                    # Server launcher
```

---

## 4. Key Functional Features (Mapped to PRD)

| PRD Section | Feature | Implementation Details |
|---|---|---|
| **FR-01 to FR-08** | Voice & Conversation | Turn-by-turn dialogue, language selection (ta/hi/en), repair phrases (*repeat, human officer*), structured field extraction. |
| **FR-09 to FR-14** | Profile & Case Management | Consented beneficiary profile, audit logging of corrections, mobile/kiosk-assisted mode. |
| **FR-15 to FR-23** | Catalog & Explainable Matching | NSQF Level 3-4 courses, 5-factor scoring (Affinity 35%, Pathway 20%, Geo 20%, Education 15%, Market demand 10%), dual English & Tamil explanations. |
| **FR-24 to FR-30** | Referral & M&E Monitoring | Referral lifecycle (Referred -> Contacted -> Enrolled -> In Training -> Completed -> Placed/Self-Employed), live funnel analytics. |
| **Section 10** | Security & Governance | Non-discriminatory matching, role-based logs, advisory disclaimers. |

---

## 5. How to Run JEEVDESK

1. **Launch Server:**
   ```powershell
   python d:\PROJECTS\SIH2026\jeevdesk\run_server.py
   ```
2. **Access Web Application:**
   Open your web browser at:
   ```
   http://127.0.0.1:8000
   ```
   - **Beneficiary Voice Mode:** Click the microphone icon or quick speech prompts to conduct the guided voice interview in Tamil, English, or Hindi.
   - **Recommendations Tab:** Inspect the explainable NSQF pathway matches and feature contribution breakdown.
   - **Case Management Tab:** Track beneficiary referral progress across training hubs and enterprise clusters.
   - **M&E Analytics Tab:** View live program conversion funnels, district distributions, and compliance audit logs.
